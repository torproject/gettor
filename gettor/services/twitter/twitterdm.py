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

import configparser

from twisted.internet import defer

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
        consumer_key = self.settings.get("consumer_key")
        consumer_secret = self.settings.get("consumer_secret")
        access_key = self.settings.get("access_key")
        access_secret = self.settings.get("access_secret")
        twitter_handle = self.settings.get("twitter_handle")

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
        raise Error("{}".format(error))


    def twitter_msg_list(self):



    def twitterdm(self):
        """
        Send a twitter message for each message received. It creates a plain
        text message, and sends it via twitter APIs

        :param twitter_handle (str): email address of the recipient.
        :param text (str): subject of the message.

        :return: deferred whose callback/errback will handle the API execution
        details.
        """

        log.debug("Retrieve list of messages")

        log.debug("Creating message")


        log.debug("Calling twitter APIs.")
