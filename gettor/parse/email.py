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

import re
import dkim
import hashlib
import validate_email

from datetime import datetime
import configparser

from email import message_from_string
from email.utils import parseaddr

from twisted.python import log
from twisted.internet import defer
from twisted.enterprise import adbapi

from ..utils.db import SQLite3


class AddressError(Exception):
    """
    Error if email address is not valid or it can't be normalized.
    """
    pass


class DKIMError(Exception):
    """
    Error if DKIM signature verification fails.
    """
    pass


class EmailParser(object):
    """Class for parsing email requests."""

    def __init__(self, settings, to_addr=None, dkim=False):
        """
        Constructor.

        param (Boolean) dkim: Set dkim verification to True or False.
        """
        self.settings = settings
        self.dkim = dkim
        self.to_addr = to_addr


    def parse(self, msg_str):
        """
        Parse message content. Check if email address is well formed, if DKIM
        signature is valid, and prevent service flooding. Finally, look for
        commands to process the request. Current commands are:

            - links: request links for download.
            - help: help request.

        :param msg_str (str): incomming message as string.

        :return dict with email address and command (`links` or `help`).
        """

        platforms = self.settings.get("platforms")
        log.msg("Building email message from string.", system="email parser")
        msg = message_from_string(msg_str)

        # Normalization will convert <Alice Wonderland> alice@wonderland.net
        # into alice@wonderland.net
        name, norm_addr = parseaddr(msg['From'])
        to_name, norm_to_addr = parseaddr(msg['To'])
        log.msg(
            "Normalizing and validating FROM email address.",
            system="email parser"
        )

        # Validate_email will do a bunch of regexp to see if the email address
        # is well address. Additional options for validate_email are check_mx
        # and verify, which check if the SMTP host and email address exist.
        # See validate_email package for more info.
        if norm_addr and validate_email.validate_email(norm_addr):
            log.msg(
                "Email address normalized and validated.",
                system="email parser"
            )
        else:
            log.err(
                "Error normalizing/validating email address.",
                system="email parser"
            )
            raise AddressError("Invalid email address {}".format(msg['From']))

        hid = hashlib.sha256(norm_addr.encode('utf-8'))
        log.msg(
            "Request from {}".format(hid.hexdigest()), system="email parser"
        )

        if self.to_addr:
            if self.to_addr != norm_to_addr:
                log.msg("Got request for a different instance of gettor")
                log.msg("Intended recipient: {}".format(norm_to_addr))
                return {}

        # DKIM verification. Simply check that the server has verified the
        # message's signature
        if self.dkim:
            log.msg("Checking DKIM signature.", system="email parser")
            # Note: msg.as_string() changes the message to conver it to
            # string, so DKIM will fail. Use the original string instead
            if dkim.verify(msg_str):
                log.msg("Valid DKIM signature.", system="email parser")
            else:
                log.msg("Invalid DKIM signature.", system="email parser")
                username, domain = norm_addr.split("@")
                raise DkimError(
                    "DKIM failed for {} at {}".format(
                        hid.hexdigest(), domain
                    )
                )

        # Search for commands keywords
        subject_re = re.compile(r"Subject: (.*)\r\n")
        subject = subject_re.search(msg_str)

        request = {
            "id": norm_addr,
            "command": None,
            "platform": None,
            "service": "email"
        }

        if subject:
            subject = subject.group(1)
            for word in re.split(r"\s+", subject.strip()):
                if word.lower() in platforms:
                    request["command"] = "links"
                    request["platform"] = word.lower()
                    break
                if word.lower() == "help":
                    request["command"] = "help"
                    break

        if not request["command"]:
            for word in re.split(r"\s+", msg_str.strip()):
                if word.lower() in platforms:
                    request["command"] = "links"
                    request["platform"] = word.lower()
                    break
                if word.lower() == "help":
                    request["command"] = "help"
                    break

        return request

    @defer.inlineCallbacks
    def parse_callback(self, request):
        """
        Callback invoked when the message has been parsed. It stores the
        obtained information in the database for further processing by the
        Sendmail service.

        :param (dict) request: the built request based on message's content.
        It contains the `email_addr` and command `fields`.

        :return: deferred whose callback/errback will log database query
        execution details.
        """
        email_requests_limit = self.settings.get("email_requests_limit")
        log.msg(
            "Found request for {}.".format(request['command']),
            system="email parser"
        )

        if request["command"]:
            now_str = datetime.now().strftime("%Y%m%d%H%M%S")
            dbname = self.settings.get("dbname")
            conn = SQLite3(dbname)

            hid = hashlib.sha256(request['id'].encode('utf-8'))
            # check limits first
            num_requests = yield conn.get_num_requests(
                id=hid.hexdigest(), service=request['service']
            )

            if num_requests[0][0] > email_requests_limit:
                log.msg(
                    "Discarded. Too many requests from {}.".format(
                        hid.hexdigest
                    ), system="email parser"
            )

            else:
                conn.new_request(
                    id=request['id'],
                    command=request['command'],
                    platform=request['platform'],
                    service=request['service'],
                    date=now_str,
                    status="ONHOLD",
                )

    def parse_errback(self, error):
        """
        Errback if we don't/can't parse the message's content.
        """
        log.msg(
            "Error while parsing email content: {}.".format(error),
            system="email parser"
        )