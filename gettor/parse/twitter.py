# -*- coding: utf-8 -*-
#
# This file is part of GetTor, a Tor Browser distribution system.
#
# :authors: isra <hiro@torproject.org>
#           see also AUTHORS file
#
# :copyright:   (c) 2008-2014, The Tor Project, Inc.
#               (c) 2019, Hiro
#
# :license: This is Free Software. See LICENSE for license information.

from __future__ import absolute_import

import re
import dkim
import hashlib

from datetime import datetime
import configparser

from twisted.python import log
from twisted.internet import defer
from twisted.enterprise import adbapi

from ..utils.db import SQLite3
from ..utils import strings


class TwitterParser(object):
    """Class for parsing twitter message requests."""

    def __init__(self, settings, twitter_id=None):
        """
        Constructor.
        """
        self.settings = settings
        self.twitter_id = twitter_id


    def build_request(self, msg_text, twitter_id, languages, platforms):

        request = {
            "id": twitter_id,
            "command": None,
            "platform": None,
            "language": "en",
            "service": "twitter"
        }

        if msg_text:
            for word in re.split(r"\s+", msg_text.strip()):
                if word.lower() in languages:
                    request["language"] = word.lower()
                if word.lower() in platforms:
                    request["command"] = "links"
                    request["platform"] = word.lower()
                if word.lower() == "help":
                    request["command"] = "help"
                    break

        return request


    def parse(self, msg, twitter_id):
        """
        Parse message content. Prevent service flooding. Finally, look for
        commands to process the request. Current commands are:

            - links: request links for download.
            - help: help request.

        :param msg_str (str): incomming message as string.

        :return dict with email address and command (`links` or `help`).
        """

        log.msg("Building twitter message from string.", system="twitter parser")

        platforms = self.settings.get("platforms")
        languages = [*strings.get_locales().keys()]

        hid = hashlib.sha256(twitter_id.encode('utf-8'))
        log.msg(
            "Request from {}".format(hid.hexdigest()), system="twitter parser"
        )

        request = self.build_request(msg, twitter_id, languages, platforms)

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
        twitter_requests_limit = self.settings.get("twitter_requests_limit")
        log.msg(
            "Found request for {}.".format(request['command']),
            system="twitter parser"
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

            if num_requests[0][0] > twitter_requests_limit:
                log.msg(
                    "Discarded. Too many requests from {}.".format(
                        hid.hexdigest
                    ), system="twitter parser"
            )

            else:
                conn.new_request(
                    id=request['id'],
                    command=request['command'],
                    platform=request['platform'],
                    language=request['language'],
                    service=request['service'],
                    date=now_str,
                    status="ONHOLD",
                )

    def parse_errback(self, error):
        """
        Errback if we don't/can't parse the message's content.
        """
        log.msg(
            "Error while parsing twitter message content: {}.".format(error),
            system="twitter parser"
        )
