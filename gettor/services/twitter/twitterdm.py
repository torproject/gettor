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

import gettext
import hashlib
import json

import configparser

from twisted.internet import defer

from ...parse.twitter import TwitterParser
from ...utils.twitter import Twitter
from ...utils.db import SQLite3 as DB
from ...utils.commons import log
from ...utils import strings

class Twitterdm(object):
    """
    Class for sending twitter replies to `help` and `links` requests.
    """
    def __init__(self, settings):
        """
        Constructor. It opens and stores a connection to the database.
        :dbname: reads from configs

        """
        self.settings = settings
        dbname = self.settings.get("dbname")
        self.twitter = Twitter(settings)
        self.conn = DB(dbname)


    def get_interval(self):
        """
        Get time interval for service periodicity.

        :return: time interval (float) in seconds.
        """
        return self.settings.get("twitter_interval")


    def twitter_callback(self, message):
        """
        Callback invoked after a message has been sent.

        :param message (string): Success details from the server.
        """
        log.info("Message sent successfully.")


    def twitter_errback(self, error):
        """
        Errback if we don't/can't send the message.
        """
        log.debug("Could not send message.")
        raise RuntimeError("{}".format(error))


    def twitterdm(self, twitter_id, message):
        """
        Send a twitter message for each message received. It creates a plain
        text message, and sends it via twitter APIs

        :param twitter_id (str): twitter_id of the recipient.
        :param message (str): text of the message.

        :return: deferred whose callback/errback will handle the API execution
        details.
        """
        return send_tweet()


    def send_tweet(self):
        post_data = self.twitter.post_message(
            twitter_id, message
        )
        if post_data.status_code == 200:
            self.twitter_callback
        else:
            self.twitter_errback

        return post_data

    @defer.inlineCallbacks
    def get_new(self):
        """
        Get new requests to process. This will define the `main loop` of
        the Twitter service.
        """

        log.debug("Retrieve list of messages")
        data = self.twitter.twitter_data()

        for e in data['events']:

            message_id = { "id": e['id'], "twitter_handle": e['message_create']['sender_id'] }

            log.debug("Parsing message")
            tp = TwitterParser(self.settings, message_id)
            yield defer.maybeDeferred(
                tp.parse, e['message_create']['message_data']['text'], message_id
            ).addCallback(tp.parse_callback).addErrback(tp.parse_errback)

        # Manage help and links messages separately
        help_requests = yield self.conn.get_requests(
            status="ONHOLD", command="help", service="twitter"
        )

        link_requests = yield self.conn.get_requests(
            status="ONHOLD", command="links", service="twitter"
        )

        if help_requests:
            strings.load_strings("en")
            try:
                log.info("Got new help request.")

                for request in help_requests:
                    ids = json.loads("{}".format(request[0].replace("'", '"')))
                    message_id = ids['id']
                    twitter_id = ids['twitter_handle']
                    date = request[5]

                    hid = hashlib.sha256(twitter_id.encode('utf-8'))
                    log.info(
                        "Sending help message to {}.".format(
                            hid.hexdigest()
                        )
                    )

                    yield self.twitterdm(
                        twitter_id=twitter_id,
                        message=strings._("help_body")
                    )

                    yield self.conn.update_stats(
                        command="help", platform='', language='en',
                        service="twitter"
                    )

                    yield self.conn.update_request(
                        id=request[0], hid=hid.hexdigest(), status="SENT",
                        service="twitter", date=date
                    )

            except RuntimeError as e:
                log.info("Error sending twitter message: {}.".format(e))

        elif link_requests:
            try:
                log.info("Got new links request.")

                for request in link_requests:
                    ids = json.loads("{}".format(request[0].replace("'", '"')))
                    message_id = ids['id']
                    twitter_id = ids['twitter_handle']
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

                    hid = hashlib.sha256(twitter_id.encode('utf-8'))
                    log.info(
                        "Sending links to {}.".format(
                            hid.hexdigest()
                        )
                    )

                    yield self.twitterdm(
                        twitter_id=twitter_id,
                        body=body_msg
                    )

                    yield self.conn.update_stats(
                        command="links", platform=platform, language=locale,
                        service="twitter"
                    )

                    yield self.conn.update_request(
                        id=request[0], hid=hid.hexdigest(), status="SENT",
                        service="twitter", date=date
                    )

            except RuntimeError as e:
                log.info("Error sending message: {}.".format(e))
        else:
            log.debug("No pending twitter requests. Keep waiting.")
