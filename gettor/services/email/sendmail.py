# -*- coding: utf-8 -*-
#
# This file is part of GetTor, a Tor Browser distribution system.
#
# :authors: isra <ilv@torproject.org>
#           see also AUTHORS file
#
# :copyright:   (c) 2008-2014, The Tor Project, Inc.
#               (c) 2014-2018, Israel Leiva
#
# :license: This is Free Software. See LICENSE for license information.

from __future__ import absolute_import

import hashlib

import configparser
from email.mime.text import MIMEText

from twisted.internet import defer
from twisted.mail import smtp

from ...utils.db import SQLite3 as DB
from ...utils.commons import log
from ...utils import strings


from email.mime.text import MIMEText
class Sendmail(object):
    """
    Class for sending email replies to `help` and `links` requests.
    """
    def __init__(self, settings):
        """
        Constructor. It opens and stores a connection to the database.
        :dbname: reads from configs
        """
        self.settings = settings
        dbname = self.settings.get("dbname")
        self.conn = DB(dbname)

    def __del__(self):
        del self.conn

    def get_interval(self):
        """
        Get time interval for service periodicity.

        :return: time interval (float) in seconds.
        """
        return self.settings.get("sendmail_interval")


    def sendmail_callback(self, message):
        """
        Callback invoked after an email has been sent.

        :param message (string): Success details from the server.
        """
        log.debug("Email sent successfully.")

    def sendmail_errback(self, error):
        """
        Errback if we don't/can't send the message.
        """
        log.warn("Could not send email.")
        raise error

    def sendmail(self, email_addr, subject, body):
        """
        Send an email message. It creates a plain text message, set headers
        and content and finally send it.

        :param email_addr (str): email address of the recipient.
        :param subject (str): subject of the message.
        :param content (str): content of the message.

        :return: deferred whose callback/errback will handle the SMTP
        execution details.
        """
        log.debug("Creating plain text email")
        message = MIMEText(body)

        message['Subject'] = subject
        message['From'] = self.settings.get("sendmail_addr")
        message['To'] = email_addr

        log.debug("Calling asynchronous sendmail.")

        return smtp.sendmail(
            self.settings.get("sendmail_host"), self.settings.get("sendmail_addr"), email_addr, message,
            requireTransportSecurity=True
        ).addCallback(self.sendmail_callback).addErrback(self.sendmail_errback)

    def build_locale_string(self, locales):
        locale_string = ""
        for locale in locales:
            locale_string += "\t" + locale[0] + "\n"
        return locale_string

    def build_help_body_message(self, locale_string):
        body_msg = strings._("body_intro")
        body_msg += strings._("help_body_intro")
        body_msg += strings._("help_body_support")
        body_msg += "\twindows\n\tlinux\n\tosx\n\n"
        body_msg += strings._("help_body_respond")
        body_msg += strings._("help_body_locale")
        body_msg += locale_string + "\n"
        body_msg += strings._("help_body_example").format("Windows", "Arabic", "windows ar")

        return body_msg


    def build_link_strings(self, links, platform, locale):
        """
        Build the links strings
        """

        link_msg = ""

        for link in links:
            provider = link[5]
            version = link[4]
            arch = link[3]
            url = link[0]
            file = link[7]
            sig_url = url + ".asc"

            link_str = "\t{}: {}\n".format(provider, url)

            link_str += "\tSignature file: {}\n".format(sig_url)

            link_msg = "{}\n{}".format(link_msg, link_str)

        return link_msg, file


    def build_body_message(self, link_msg, platform, file):
        signature_strings = {
            "windows":"links_body_windows",
            "linux":"links_body_linux",
            "osx":"links_body_osx"
        }
        signature_cmds = {
            "windows":"gpgv --keyring .\\tor.keyring Downloads\\{0}.asc Downloads\\{0}",
            "linux":"gpgv --keyring ./tor.keyring ~/Downloads/{}{{.asc,}}",
            "osx":"gpgv --keyring ./tor.keyring ~/Downloads/{}{{.asc,}}"
        }
        body_msg = strings._("body_intro")
        body_msg += strings._("links_body_platform").format(platform)
        body_msg += strings._("links_body_step1").format(link_msg)
        body_msg += strings._("links_body_archive").format(file)
        body_msg += strings._("links_body_internet_archive")
        body_msg += strings._("links_body_google_drive")
        body_msg += strings._("links_body_step2")
        body_msg += strings._(signature_strings[platform])
        body_msg += strings._("links_body_all").format(signature_cmds[platform].format(file))
        body_msg += strings._("links_body_step3")

        return body_msg


    @defer.inlineCallbacks
    def get_new(self):
        """
        Get new requests to process. This will define the `main loop` of
        the Sendmail service.
        """

        # Manage help and links messages separately
        requests = yield self.conn.get_requests(
            status="ONHOLD", service="email"
        )

        strings.load_strings("en")
        try:

            for request in requests:
                id = request[0]
                command = request[1]
                platform = request[2]
                language = request[3]
                date = request[5]

                if not language:
                    language = 'en'

                body_msg =""
                subject_msg =""

                if command == "help":

                    locales = yield self.conn.get_locales()
                    locale_string = self.build_locale_string(locales)

                    # build message
                    body_msg = self.build_help_body_message(locale_string)
                    subject_msg = strings._("help_subject")

                elif command == "links":
                    log.debug("Getting links for {} {}.".format(platform, language))
                    links = yield self.conn.get_links(
                        platform=platform, language=language, status="ACTIVE"
                    )

                    # build message
                    link_msg, file = self.build_link_strings(links, platform, language)
                    body_msg = self.build_body_message(link_msg, platform, file)
                    subject_msg = strings._("links_subject")
                else:
                    log.warn("Invalid gettor command {}.".format(command))
                    yield self.conn.remove_request(
                        id=id, service="email", date=date
                    )

                log.debug("Sending {} message.".format(request[1]))

                yield self.sendmail(
                    email_addr=id,
                    subject=subject_msg,
                    body=body_msg
                )

                yield self.conn.update_stats(
                    command=command, platform=platform, language=language,
                    service="email"
                )

                yield self.conn.remove_request(
                    id=id, service="email", date=date
                )

        except smtp.SMTPClientError as e:
            if e.code == 501: # Bad recipient address syntax
                yield self.conn.remove_request(
                    id=id, service="email", date=date
                )
            log.error(
                strings.redact_emails("Error sending email:{}.".format(e))
                )

        except Exception as e:
            log.error(
                strings.redact_emails("Error sending email:{}.".format(e))
                )
