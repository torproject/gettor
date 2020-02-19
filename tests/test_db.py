#!/usr/bin/env python3
import pytest
import pytest_twisted
from twisted.trial import unittest

from . import conftests

class DatabaseTests(unittest.TestCase):

    # Fail any tests which take longer than 15 seconds.
    timeout = 15
    def setUp(self):
        self.settings = conftests.options.parse_settings("en","./gettor.conf.json")
        self.locales = conftests.strings.get_locales()

        self.conn = conftests.SQLite3(self.settings.get("dbname"))

    def tearDown(self):
        print("tearDown()")
        del self.conn

    @pytest_twisted.inlineCallbacks
    def test_stored_locales(self):
        locales = yield self.conn.get_locales()

if __name__ == "__main__":
    unittest.main()
