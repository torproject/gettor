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

from requests_oauthlib import OAuth1Session

class Twitter(object):
    """
    Class for sending twitter commands via the API.
    """
    def __init__(self, settings):
        """
        Constructor.

        """
        self.settings = settings

        consumer_key = self.settings.get("consumer_key")
        consumer_secret = self.settings.get("consumer_secret")
        access_key = self.settings.get("access_key")
        access_secret = self.settings.get("access_secret")
        twitter_handle = self.settings.get("twitter_handle")

        self.twitter_messages_endpoint = self.settings.get("twitter_messages_endpoint")
        self.twitter_new_message_endpoint = self.settings.get("twitter_new_message_endpoint")
        self.twitter_client = self.twitter_oauth(consumer_key, consumer_secret, access_key, access_secret)

    def twitter_oauth(self, consumer_key, consumer_secret, access_key, access_secret):
        tw_client = OAuth1Session(client_key=consumer_key,
                               client_secret=consumer_secret,
                               resource_owner_key=access_key,
                               resource_owner_secret=access_secret)
        return tw_client


    def twitter_data(self):
        data = self.twitter_client.get(self.twitter_messages_endpoint)
        return data.json()


    def post_message(self, twitter_id, text):
        message = {
            "event": {
                "type": "message_create",
                "message_create": {
                    "target": {"recipient_id": twitter_id },
                    "message_data": {"text": text }
                }
            }
        }

        data = self.twitter_client.post(self.twitter_new_message_endpoint, json=message)
        return data
