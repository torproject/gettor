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

import gettext
import hashlib

import configparser
from email import encoders
from email import mime
from email.mime.text import MIMEText

from twisted.internet import defer
from twisted.mail.smtp import sendmail

from ...utils.db import SQLite3 as DB
from ...utils.commons import log
from ...utils import strings


class SMTPError(Exception):
    """
    Error if we can't send emails.
    """
    pass

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
        log.info("Email sent successfully.")

    def sendmail_errback(self, error):
        """
        Errback if we don't/can't send the message.
        """
        log.debug("Could not send email.")
        raise SMTPError("{}".format(error))

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

        return sendmail(
            self.settings.get("sendmail_host"), self.settings.get("sendmail_addr"), email_addr, message,
            requireTransportSecurity=True
        ).addCallback(self.sendmail_callback).addErrback(self.sendmail_errback)


    @defer.inlineCallbacks
    def get_new(self):
        """
        Get new requests to process. This will define the `main loop` of
        the Sendmail service.
        """

        # Manage help and links messages separately
        help_requests = yield self.conn.get_requests(
            status="ONHOLD", command="help", service="email"
        )

        link_requests = yield self.conn.get_requests(
            status="ONHOLD", command="links", service="email"
        )

        if help_requests:
            strings.load_strings("en")
            try:
                log.info("Got new help request.")

                for request in help_requests:
                    id = request[0]
                    date = request[5]

                    hid = hashlib.sha256(id.encode('utf-8'))
                    log.info(
                        "Sending help message to {}.".format(
                            hid.hexdigest()
                        )
                    )

                    yield self.sendmail(
                        email_addr=id,
                        subject=strings._("help_subject"),
                        body=strings._("help_body")
                    )

                    yield self.conn.update_stats(
                        command="help", platform='', language='en',
                        service="email"
                    )

                    yield self.conn.update_request(
                        id=id, hid=hid.hexdigest(), status="SENT",
                        service="email", date=date
                    )

            except SMTPError as e:
                log.info("Error sending email: {}.".format(e))

        elif link_requests:
            try:
                log.info("Got new links request.")

                for request in link_requests:
                    id = request[0]
                    date = request[5]
                    platform = request[2]
                    language = request[3]

                    if not language:
                        language = 'en'

                    locales = strings.get_locales()

                    strings.load_strings(language)
                    locale = locales[language]['locale']

                    log.info("Getting links for {}.".format(platform))
                    links = yield self.conn.get_links(
                        platform=platform, language=locale, status="ACTIVE"
                    )

                    # build message
                    link_msg = None
                    file = ""

                    for link in links:
                        provider = link[5]
                        version = link[4]
                        arch = link[3]
                        url = link[0]
                        file = link[7]
                        sig_url = url + ".asc"

                        link_str = "Tor Browser {} for {}-{}-{} ({}): {}\n".format(
                            version, platform, locale, arch, provider, url
                        )

                        link_str += "Signature file: {}\n".format(sig_url)

                        if link_msg:
                            link_msg = "{}\n{}".format(link_msg, link_str)
                        else:
                            link_msg = link_str

                    body_msg = strings._("links_body").format(platform, link_msg, file)
                    subject_msg = strings._("links_subject")

                    hid = hashlib.sha256(id.encode('utf-8'))
                    log.info(
                        "Sending links to {}.".format(
                            hid.hexdigest()
                        )
                    )

                    yield self.sendmail(
                        email_addr=id,
                        subject=subject_msg,
                        body=body_msg
                    )

                    yield self.conn.update_stats(
                        command="links", platform=platform, language=locale,
                        service="email"
                    )

                    yield self.conn.update_request(
                        id=id, hid=hid.hexdigest(), status="SENT",
                        service="email", date=date
                    )

            except SMTPError as e:
                log.info("Error sending email: {}.".format(e))
        else:
            log.debug("No pending email requests. Keep waiting.")
