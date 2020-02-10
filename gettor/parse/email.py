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
import io
import dkim
import hashlib

from datetime import datetime
import configparser

from email import message_from_string
from email.utils import parseaddr

from twisted.python import log
from twisted.internet import defer

from ..utils.db import SQLite3
from ..utils import validate_email

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
        self.locales = []
        self.platforms = self.settings.get("platforms")
        self.conn = SQLite3(self.settings.get("dbname"))

    def __del__(self):
        del self.conn

    def normalize(self, msg):
        # Normalization will convert <Alice Wonderland> alice@wonderland.net
        # into alice@wonderland.net
        name, norm_addr = parseaddr(msg['From'])
        to_name, norm_to_addr = parseaddr(msg['To'])
        log.msg(
            "Normalizing and validating FROM email address.",
            system="email parser"
        )
        return name, norm_addr, to_name, norm_to_addr


    def validate(self, norm_addr, msg):
        # Validate_email will do a bunch of regexp to see if the email address
        # is well address. Additional options for validate_email are check_mx
        # and verify, which check if the SMTP host and email address exist.
        # See validate_email package for more info.
        if norm_addr and validate_email.validate_email(norm_addr):
            log.msg(
                "Email address normalized and validated.",
                system="email parser"
            )
            return True

        else:
            log.err(
                "Error normalizing/validating email address.",
                system="email parser"
            )
            raise AddressError("Invalid email address {}".format(msg['From']))


    def dkim_verify(self, msg_str, norm_addr):
        # DKIM verification. Simply check that the server has verified the
        # message's signature
        if self.dkim:
            log.msg("Checking DKIM signature.", system="email parser")
            # Note: msg.as_string() changes the message to conver it to
            # string, so DKIM will fail. Use the original string instead
            if dkim.verify(msg_str):
                log.msg("Valid DKIM signature.", system="email parser")
                return True
            else:
                log.msg("Invalid DKIM signature.", system="email parser")
                username, domain = norm_addr.split("@")
                raise DkimError(
                    "DKIM failed for {} at {}".format(
                        hid.hexdigest(), domain
                    )
                )
        # Is this even useful like this?
        else:
            return True

    def parse_keywords(self, text, request):

        buf = io.StringIO(text)
        for line in buf:
            if len(line.strip()) > 0 and line.strip()[0] == ">":
                continue
            for word in re.split(r"\s+", line.strip()):
                for locale in self.locales:
                    if word.lower() == locale.lower():
                        request["language"] = locale
                    elif (not request["language"]) and (word.lower()[:2] ==
                            locale.lower()[:2]):
                        request["language"] = locale
                if word.lower() in self.platforms:
                    request["command"] = "links"
                    request["platform"] = word.lower()
                if (not request["command"])  and word.lower() == "help":
                    request["command"] = "help"
        return request

    def build_request(self, msg_str, norm_addr):
        # Search for commands keywords
        subject_re = re.compile(r"Subject: (.*)\r\n")
        subject = subject_re.search(msg_str)

        request = {
            "id": norm_addr,
            "command": None,
            "platform": None,
            "language": None,
            "service": "email"
        }

        if subject:
            subject = subject.group(1)
            request = self.parse_keywords(subject, request)

        # Always parse the body too, to see if there's more specific information
        request = self.parse_keywords(msg_str, request)

        if not request["language"]:
            request["language"] = "en-US"

        if not request["command"]:
            request["command"] = "help"

        return request


    def too_many_requests(self, hid, test_hid, num_requests, limit):
        if hid == test_hid:
            return False
        elif num_requests < limit:
            return False
        else:
            return True

    @defer.inlineCallbacks
    def get_locales(self):

        locales = yield self.conn.get_locales()
        for l in locales:
            self.locales.append(l[0])


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

        log.msg("Building email message from string.", system="email parser")

        msg = message_from_string(msg_str)

        name, norm_addr, to_name, norm_to_addr = self.normalize(msg)

        try:
            self.validate(norm_addr, msg)
        except AddressError as e:
            log.message("Address error: {}".format(e.args))

        hid = hashlib.sha256(norm_addr.encode('utf-8'))
        log.msg(
            "Request from {}".format(hid.hexdigest()), system="email parser"
        )

        if self.to_addr:
            if self.to_addr != norm_to_addr:
                log.msg("Got request for a different instance of gettor")
                log.msg("Intended recipient: {}".format(norm_to_addr))
                return {}

        try:
            self.dkim_verify(msg_str, norm_addr)
        except ValueError as e:
            log.msg("DKIM error: {}".format(e.args))

        request = self.build_request(msg_str, norm_addr)

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
        now_str = datetime.now().strftime("%Y%m%d%H%M%S")
        dbname = self.settings.get("dbname")
        test_hid = self.settings.get("test_hid")

        if request["command"]:

            hid = hashlib.sha256(request['id'].encode('utf-8')).hexdigest()
            request_service = request['service']

            log.msg(
                "Found request for {}.".format(request['command']),
                system="email parser"
            )

            num_requests = yield self.conn.get_num_requests(
                id=hid, service=request_service
            )

            check = self.too_many_requests(
                hid, test_hid, num_requests[0][0], email_requests_limit
            )

            if check:
                log.msg(
                    "Discarded. Too many requests from {}.".format(
                        hid
                    ), system="email parser"
                )
            else:
                self.conn.new_request(
                    id=request['id'],
                    command=request['command'],
                    platform=request['platform'],
                    language=request['language'],
                    service=request['service'],
                    date=now_str,
                    status="ONHOLD",
                )
        else:
            log.msg(
                "Request not found",
                system="email parser"
            )

    def parse_errback(self, error):
        """
        Errback if we don't/can't parse the message's content.
        """
        log.msg(
            "Error while parsing email content: {}.".format(error),
            system="email parser"
        )
