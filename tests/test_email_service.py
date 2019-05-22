#!/usr/bin/env python3
import pytest
from twisted.trial import unittest
from twisted.internet import defer, reactor
from twisted.internet import task

from . import conftests

class EmailServiceTests(unittest.TestCase):

    # Fail any tests which take longer than 15 seconds.
    timeout = 15
    def setUp(self):
        self.settings = conftests.options.parse_settings()
        self.sm_client = conftests.sendmail.Sendmail(self.settings)

    def tearDown(self):
        print("tearDown()")

    def test_get_interval(self):
        self.assertEqual(self.settings.get("sendmail_interval"), self.sm_client.get_interval())

    def test_help_email_parser(self):
        ep = conftests.EmailParser(self.settings, "gettor@torproject.org")
        request = ep.parse("From: \"silvia [hiro]\" <hiro@torproject.org>\n Subject: help\n Reply-To: hiro@torproject.org \nTo: gettor@torproject.org")
        self.assertEqual(request["command"], "help")

    def test_language_email_parser(self):
        ep = conftests.EmailParser(self.settings, "gettor@torproject.org")
        request = ep.parse("From: \"silvia [hiro]\" <hiro@torproject.org>\n Subject: \r\n Reply-To: hiro@torproject.org \nTo: gettor@torproject.org\n osx en")
        self.assertEqual(request["command"], "links")
        self.assertEqual(request["platform"], "osx")
        self.assertEqual(request["language"], "en")


if __name__ == "__main__":
    unittest.main()
