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
        self.locales = conftests.strings.get_locales()

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

    def test_remove_limits(self):
        ep = conftests.EmailParser(self.settings, "gettor@torproject.org")
        msg_str = "From: \"GetTor Test\" <test.gettor.browser@gmail.com>\n Subject: \r\n Reply-To: test.gettor.browser@gmail.com \nTo: gettor@torproject.org\r\n osx es"
        msg = conftests.message_from_string(msg_str)
        languages = [*self.locales.keys()]
        platforms = self.settings.get('platforms')
        request = ep.build_request(msg_str, "hiro@torproject.org", languages, platforms)
        email_requests_limit = self.settings.get("email_requests_limit")
        check = check_num_request(request['id'], request['service'], email_request_limit)
        assert check

    def test_language_email_parser(self):
        ep = conftests.EmailParser(self.settings, "gettor@torproject.org")
        request = ep.parse("From: \"silvia [hiro]\" <hiro@torproject.org>\n Subject: \r\n Reply-To: hiro@torproject.org \nTo: gettor@torproject.org\n osx en")
        self.assertEqual(request["command"], "links")
        self.assertEqual(request["platform"], "osx")
        self.assertEqual(request["language"], "en")


if __name__ == "__main__":
    unittest.main()
