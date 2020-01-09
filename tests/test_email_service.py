#!/usr/bin/env python3
import pytest
import hashlib
from datetime import datetime
from twisted.trial import unittest
from twisted.internet import defer, reactor
from twisted.internet import task

from . import conftests

class EmailServiceTests(unittest.TestCase):

    # Fail any tests which take longer than 15 seconds.
    timeout = 15
    def setUp(self):
        self.settings = conftests.options.parse_settings("en","./gettor.conf.json")
        self.sm_client = conftests.Sendmail(self.settings)
        self.locales = conftests.strings.get_locales()
        self.links = [
            [
                "https://gitlab.com/thetorproject/gettorbrowser/raw/torbrowser-releases/TorBrowser-9.0.3-osx64_en-US.dmg",
                "osx",
                "en-US",
                "64",
                "9.0.3",
                "gitlab",
                "ACTIVE",
                "TorBrowser-9.0.3-osx64_en-US.dmg"
            ]
        ]

    def tearDown(self):
        print("tearDown()")

    def test_get_interval(self):
        self.assertEqual(self.settings.get("sendmail_interval"), self.sm_client.get_interval())

    def test_help_email_parser(self):
        ep = conftests.EmailParser(self.settings, "gettor@torproject.org")
        request = ep.parse("From: \"silvia [hiro]\" <hiro@torproject.org>\n Subject: help\n Reply-To: hiro@torproject.org \nTo: gettor@torproject.org")
        self.assertEqual(request["command"], "help")

    def test_normalize_msg(self):
        ep = conftests.EmailParser(self.settings, "gettor@torproject.org")
        msg_str = "From: \"silvia [hiro]\" <hiro@torproject.org>\n Subject: help\n Reply-To: hiro@torproject.org \nTo: gettor@torproject.org"
        msg = conftests.message_from_string(msg_str)
        request = ep.normalize(msg)
        self.assertEqual(request, ('silvia [hiro]', 'hiro@torproject.org', '', 'gettor@torproject.org'))

    def test_validate_msg(self):
        ep = conftests.EmailParser(self.settings, "gettor@torproject.org")
        msg_str = "From: \"silvia [hiro]\" <hiro@torproject.org>\n Subject: help\n Reply-To: hiro@torproject.org \nTo: gettor@torproject.org"
        msg = conftests.message_from_string(msg_str)
        request = ep.validate("hiro@torproject.org", msg)
        assert request

    def test_dkim_verify(self):
        ep = conftests.EmailParser(self.settings, "gettor@torproject.org")
        msg_str = "From: \"silvia [hiro]\" <hiro@torproject.org>\n Subject: help\n Reply-To: hiro@torproject.org \nTo: gettor@torproject.org"
        msg = conftests.message_from_string(msg_str)
        request = ep.dkim_verify(msg, "hiro@torproject.org")
        assert request

    def test_build_request(self):
        ep = conftests.EmailParser(self.settings, "gettor@torproject.org")
        msg_str = "From: \"silvia [hiro]\" <hiro@torproject.org>\n Subject: \r\n Reply-To: hiro@torproject.org \nTo: gettor@torproject.org\r\n osx es"
        msg = conftests.message_from_string(msg_str)
        languages = [*self.locales.keys()]
        platforms = self.settings.get('platforms')
        request = ep.build_request(msg_str, "hiro@torproject.org", languages, platforms)
        self.assertEqual(request["command"], "links")
        self.assertEqual(request["platform"], "osx")
        self.assertEqual(request["language"], "es")

    def test_too_many_request_exclude(self):
        ep = conftests.EmailParser(self.settings, "gettor@torproject.org")
        hid = "80d7054da0d3826563c7babb5453e18f3e42f932e562c5ab0434aec9df7b0625"
        limit = self.settings.get("email_requests_limit")
        num_requests = 300
        check = ep.too_many_requests(hid, self.settings.get("test_hid"), num_requests, limit)
        self.assertEqual(hid, self.settings.get("test_hid"))
        self.assertEqual(check, False)

    def test_language_email_parser(self):
        ep = conftests.EmailParser(self.settings, "gettor@torproject.org")
        request = ep.parse("From: \"silvia [hiro]\" <hiro@torproject.org>\n Subject: \r\n Reply-To: hiro@torproject.org \nTo: gettor@torproject.org\n osx en")
        self.assertEqual(request["command"], "links")
        self.assertEqual(request["platform"], "osx")
        self.assertEqual(request["language"], "en")

    def test_sent_links_message(self):
        ep = self.sm_client
        links = self.links
        link_msg, file = ep.build_link_strings(links, "osx", "en")
        assert "https://gitlab.com/thetorproject/gettorbrowser/raw/torbrowser-releases/TorBrowser-9.0.3-osx64_en-US.dmg" in link_msg
        assert "osx" in link_msg

        self.assertEqual("TorBrowser-9.0.3-osx64_en-US.dmg", file)

    def test_sent_body_message(self):
        ep = self.sm_client
        links = self.links
        link_msg, file = ep.build_link_strings(links, "osx", "en")
        body_msg = ep.build_body_message(link_msg, "osx", file)
        assert "You requested Tor Browser for osx" in body_msg

    def test_help_body_message(self):
        ep = self.sm_client
        help_msg = ep.build_help_body_message()
        assert "This is how you can request a tor browser bundle link" in help_msg


if __name__ == "__main__":
    unittest.main()
