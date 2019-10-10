#!/usr/bin/env python3
import pytest
from twisted.trial import unittest
from twisted.internet import defer, reactor
from twisted.internet import task

from . import conftests

class TwitterTests(unittest.TestCase):
    # Fail any tests which take longer than 15 seconds.
    timeout = 15
    def setUp(self):
        self.settings = conftests.options.parse_settings()
        self.tw_client = conftests.twitter.Twitter(self.settings)


    def tearDown(self):
        print("tearDown()")


    def test_load_messages(self):
        data = self.tw_client.twitter_data()
        assert data['events']


    def test_parse_tweet(self):
        e = {'type': 'message_create', 'id': '1178649287208689669', 'created_timestamp': '1569846862972', 'message_create': {'target': {'recipient_id': '2514714800'}, 'sender_id': '1467062174', 'message_data': {'text': 'windows 10', 'entities': {'hashtags': [], 'symbols': [], 'user_mentions': [], 'urls': []}}}}
        message_id = { 'id': e['id'], 'twitter_handle': e['message_create']['sender_id'] }
        message = e['message_create']['message_data']['text']
        tp = conftests.TwitterParser(self.settings, message_id)
        r = tp.parse(message, str(message_id))
        self.assertEqual(r, {'command': 'links', 'id': "{'id': '1178649287208689669', 'twitter_handle': '1467062174'}", 'language': 'en', 'platform': 'windows','service': 'twitter'})


if __name__ == "__main__":
    unittest.main()
