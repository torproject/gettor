#!/usr/bin/env python3
import pytest
from datetime import datetime
from twisted.trial import unittest

from . import conftests

class DatabaseTests(unittest.TestCase):

    # Fail any tests which take longer than 15 seconds.
    timeout = 15
    def setUp(self):
        self.settings = conftests.options.parse_settings("en","tests/test.conf.json")
        print(self.settings.get("dbname"))
        self.db = conftests.SQLite3(self.settings.get("dbname"))

    def tearDown(self):
        print("tearDown()")

    def add_dummy_requests(self, num):
        now_str = datetime.now().strftime("%Y%m%d")
        for i in (0, num):
            self.db.new_request(
                id='testid',
                command='links',
                platform='linux',
                language='en',
                service='email',
                date=now_str,
                status="ONHOLD",
            )

    def test_stored_locales(self):
        locales = self.db.get_locales()
        self.assertIn('en-US', locales)

    def test_requests(self):
        now_str = datetime.now().strftime("%Y%m%d")
        self.add_dummy_requests(2)
        num = self.db.get_num_requests("testid", "email")
        self.assertEqual(num, 2)

        requests = self.db.get_requests("ONHOLD", "links", "email")
        for request in requests:
            print(request)
            self.assertEqual(request[1], "links")
            self.assertEqual(request[4], "email")
            self.assertEqual(request[5], now_str)
            self.assertEqual(request[6], "ONHOLD")
        self.assertEqual(len(requests), 2)

        self.db.remove_request("testid", "email", now_str)
        num = self.db.get_num_requests("testid", "email")
        self.assertEqual(num, 0)

    def test_links(self):
        links = self.db.get_links("linux", "en-US", "ACTIVE")
        self.assertEqual(len(links), 2) # Right now we have github and gitlab

        for link in links:
            self.assertEqual(link[1], "linux")
            self.assertEqual(link[2], "en-US")
            self.assertEqual(link[6], "ACTIVE")
            self.assertIn(link[5], ["github", "gitlab"])

if __name__ == "__main__":
    unittest.main()
