#!/usr/bin/env python3
import pytest
import pytest_twisted
from datetime import datetime
from twisted.trial import unittest

from . import conftests

class DatabaseTests(unittest.TestCase):

    # Fail any tests which take longer than 15 seconds.
    timeout = 15
    def setUp(self):
        self.settings = conftests.options.parse_settings("en","tests/test.conf.json")
        self.locales = conftests.strings.get_locales()

        self.conn = conftests.SQLite3(self.settings.get("dbname"))

    def tearDown(self):
        print("tearDown()")
        del self.conn

    @pytest_twisted.inlineCallbacks
    def add_dummy_requests(self, num):
        now_str = datetime.now().strftime("%Y%m%d")
        for i in (0, num):
            yield self.conn.new_request(
                id='testid',
                command='links',
                platform='linux',
                language='en',
                service='email',
                date=now_str,
                status="ONHOLD",
            )

    @pytest_twisted.inlineCallbacks
    def test_stored_locales(self):
        locales = []
        ls = yield self.conn.get_locales()
        for l in ls:
            locales.append(l[0])
        self.assertIn('en-US', locales)

    @pytest_twisted.inlineCallbacks
    def test_requests(self):
        now_str = datetime.now().strftime("%Y%m%d")
        yield self.add_dummy_requests(2)
        num = yield self.conn.get_num_requests("testid", "email")
        self.assertEqual(num[0][0], 2)

        requests = yield self.conn.get_requests("ONHOLD", "links", "email")
        for request in requests:
            self.assertEqual(request[1], "links")
            self.assertEqual(request[4], "email")
            self.assertEqual(request[5], now_str)
            self.assertEqual(request[6], "ONHOLD")
        self.assertEqual(len(requests), 2)

        yield self.conn.remove_request("testid", "email", now_str)
        num = yield self.conn.get_num_requests("testid", "email")
        self.assertEqual(num[0][0], 0)

    @pytest_twisted.inlineCallbacks
    def test_links(self):
        links = yield self.conn.get_links("linux", "en-US", "ACTIVE")

        for link in links:
            self.assertEqual(link[1], "linux")
            self.assertEqual(link[2], "en-US")
            self.assertEqual(link[6], "ACTIVE")
            self.assertIn(link[5], ["github", "gitlab"])

if __name__ == "__main__":
    unittest.main()
