#!/usr/bin/env python3
import pytest
import pytest_twisted
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
        self.settings = conftests.options.parse_settings("en","tests/test.conf.json")
        self.sm_client = conftests.Sendmail(self.settings)
        self.locales = conftests.strings.get_locales()

    def tearDown(self):
        print("tearDown()")
        del self.sm_client

    def test_get_interval(self):
        self.assertEqual(self.settings.get("sendmail_interval"), self.sm_client.get_interval())

    def test_help_email_parser(self):
        ep = conftests.EmailParser(self.settings, "gettor@torproject.org")
        request = ep.parse("From: \"silvia [hiro]\" <hiro@torproject.org>\n Subject: help\n Reply-To: hiro@torproject.org \nTo: gettor@torproject.org")
        self.assertEqual(request["command"], "help")
        del ep

    def test_normalize_msg(self):
        ep = conftests.EmailParser(self.settings, "gettor@torproject.org")
        msg_str = "From: \"silvia [hiro]\" <hiro@torproject.org>\n Subject: help\n Reply-To: hiro@torproject.org \nTo: gettor@torproject.org"
        msg = conftests.message_from_string(msg_str)
        request = ep.normalize(msg)
        self.assertEqual(request, ('silvia [hiro]', 'hiro@torproject.org', '', 'gettor@torproject.org'))
        del ep

    def test_validate_msg(self):
        ep = conftests.EmailParser(self.settings, "gettor@torproject.org")
        msg_str = "From: \"silvia [hiro]\" <hiro@torproject.org>\n Subject: help\n Reply-To: hiro@torproject.org \nTo: gettor@torproject.org"
        msg = conftests.message_from_string(msg_str)
        request = ep.validate("hiro@torproject.org", msg)
        assert request
        del ep

    def test_dkim_verify(self):
        ep = conftests.EmailParser(self.settings, "gettor@torproject.org")
        msg_str = "From: \"silvia [hiro]\" <hiro@torproject.org>\n Subject: help\n Reply-To: hiro@torproject.org \nTo: gettor@torproject.org"
        msg = conftests.message_from_string(msg_str)
        request = ep.dkim_verify(msg, "hiro@torproject.org")
        assert request
        del ep

    def test_build_request(self):
        ep = conftests.EmailParser(self.settings, "gettor@torproject.org")
        msg_str = "From: \"silvia [hiro]\" <hiro@torproject.org>\n Subject: \r\n Reply-To: hiro@torproject.org \nTo: gettor@torproject.org\r\n\r\n osx es"
        msg = conftests.message_from_string(msg_str)
        ep.locales = ["es", "en"]
        request = ep.build_request(msg_str, "hiro@torproject.org")
        self.assertEqual(request["command"], "links")
        self.assertEqual(request["platform"], "osx")
        self.assertEqual(request["language"], "es")
        del ep

    def test_too_many_request_exclude(self):
        ep = conftests.EmailParser(self.settings, "gettor@torproject.org")
        hid = "80d7054da0d3826563c7babb5453e18f3e42f932e562c5ab0434aec9df7b0625"
        limit = self.settings.get("email_requests_limit")
        num_requests = 300
        check = ep.too_many_requests(hid, self.settings.get("test_hid"), num_requests, limit)
        self.assertEqual(hid, self.settings.get("test_hid"))
        self.assertEqual(check, False)
        del ep

    def test_email_parser(self):
        ep = conftests.EmailParser(self.settings, "gettor@torproject.org")
        ep.locales = ["en-US", "es-ES", "es-AR", "pt-BR", "fa"]
        request = ep.parse("From: \"silvia [hiro]\" <hiro@torproject.org>\n"
                "Subject: \r\n Reply-To: hiro@torproject.org \nTo:"
                "gettor@torproject.org\r\n\r\n")
        self.assertEqual(request["language"], "en-US")
        self.assertEqual(request["command"], "help")

        request = ep.parse("From: \"silvia [hiro]\" <hiro@torproject.org>\n"
                "Subject: \r\n Reply-To: hiro@torproject.org \nTo:"
                "gettor@torproject.org\r\n\r\n please send me tor\n")
        self.assertEqual(request["language"], "en-US")
        self.assertEqual(request["command"], "help")

        request = ep.parse("From: \"silvia [hiro]\" <hiro@torproject.org>\n"
                "Subject: \r\n Reply-To: hiro@torproject.org \nTo:"
                "gettor@torproject.org\r\n\r\nwindows\n")
        self.assertEqual(request["language"], "en-US")
        self.assertEqual(request["platform"], "windows")
        self.assertEqual(request["command"], "links")

        request = ep.parse("From: \"silvia [hiro]\" <hiro@torproject.org>\n"
                "Subject: \r\n Reply-To: hiro@torproject.org \nTo:"
                "gettor@torproject.org\r\n\r\n fa\n")
        self.assertEqual(request["language"], "fa")
        self.assertEqual(request["command"], "help")

        request = ep.parse("From: \"silvia [hiro]\" <hiro@torproject.org>\n"
                "Subject: \r\n Reply-To: hiro@torproject.org \nTo:"
                "gettor@torproject.org\r\n\r\n please help me get tor for windows\n")
        self.assertEqual(request["language"], "en-US")
        self.assertEqual(request["command"], "links")
        self.assertEqual(request["platform"], "windows")

    def test_language_email_parser(self):
        ep = conftests.EmailParser(self.settings, "gettor@torproject.org")
        ep.locales = ["en-US", "es-ES", "es-AR", "pt-BR", "fa"]
        request = ep.parse("From: \"silvia [hiro]\" <hiro@torproject.org>\n"
                "Subject: \r\n Reply-To: hiro@torproject.org \nTo:"
                "gettor@torproject.org\r\n\r\n osx en")
        self.assertEqual(request["language"], "en-US")

        request = ep.parse("From: \"silvia [hiro]\" <hiro@torproject.org>\n"
                "Subject: \r\n Reply-To: hiro@torproject.org \nTo:"
                "gettor@torproject.org\r\n\r\n osx ES")
        self.assertEqual(request["language"], "es-ES")

        request = ep.parse("From: \"silvia [hiro]\" <hiro@torproject.org>\n"
                "Subject: \r\n Reply-To: hiro@torproject.org \nTo:"
                "gettor@torproject.org\r\n\r\n osx en-US")
        self.assertEqual(request["language"], "en-US")

        request = ep.parse("From: \"silvia [hiro]\" <hiro@torproject.org>\n"
                "Subject: \r\n Reply-To: hiro@torproject.org \nTo:"
                "gettor@torproject.org\r\n\r\n linux fa")
        self.assertEqual(request["language"], "fa")

        request = ep.parse("From: \"silvia [hiro]\" <hiro@torproject.org>\n"
                "Subject: \r\n Reply-To: hiro@torproject.org \nTo:"
                "gettor@torproject.org\r\n\r\n osx es")
        self.assertEqual(request["language"], "es-ES")

        request = ep.parse("From: \"silvia [hiro]\" <hiro@torproject.org>\n"
                "Subject: \r\n Reply-To: hiro@torproject.org \nTo:"
                "gettor@torproject.org\r\n\r\n linux zz")
        self.assertEqual(request["language"], "en-US")

        request = ep.parse("From: \"silvia [hiro]\" <hiro@torproject.org>\n"
                "Subject: \r\n Reply-To: hiro@torproject.org \nTo:"
                "gettor@torproject.org\r\n\r\n linux pt-PT")
        self.assertEqual(request["language"], "pt-BR")

        request = ep.parse("From: \"silvia [hiro]\" <hiro@torproject.org>\n"
                "Subject: \r\n Reply-To: hiro@torproject.org \nTo:"
                "gettor@torproject.org\r\n\r\n linux es-AR")
        self.assertEqual(request["language"], "es-AR")

        request = ep.parse("From: \"silvia [hiro]\" <hiro@torproject.org>\n"
                "Subject: linux es\r\n Reply-To: hiro@torproject.org \nTo:"
                "gettor@torproject.org\r\n\r\n linux es-AR")
        self.assertEqual(request["language"], "es-AR")

        request = ep.parse("From: \"silvia [hiro]\" <hiro@torproject.org>\n"
                "Subject: linux es\r\n Reply-To: hiro@torproject.org \nTo:"
                "gettor@torproject.org\r\n\r\n linux")
        self.assertEqual(request["language"], "es-ES")

        request = ep.parse("From: \"silvia [hiro]\" <hiro@torproject.org>\n"
                "Subject: linux es-AR\r\n Reply-To: hiro@torproject.org \nTo:"
                "gettor@torproject.org\r\n\r\n linux es")
        self.assertEqual(request["language"], "es-AR")
        del ep

    def test_body_subject_parser(self):
        ep = conftests.EmailParser(self.settings, "gettor@torproject.org")
        ep.locales = ["en-US", "es-ES", "es-AR", "pt-BR", "fa"]
        request = ep.parse(
            "To: gettor@torproject.org\r\n"
            "From: Cecylia Bocovich <cohosh@torproject.org>\r\n"
            "Subject: windows es\r\n"
            "Message-ID: <0befc58c-c94d-c262-9597-4365122c04b4@torproject.org>\r\n"
            "Date: Mon, 11 Jan 2021 11:28:37 -0500\r\n"
            "MIME-Version: 1.0\r\n"
            "Content-Type: text/plain; charset=utf-8\r\n"
            "Content-Language: en-US\r\n"
            "Content-Transfer-Encoding: 7bit\r\n"
            "\r\n"
            "windows es\r\n"
        )
        self.assertEqual(request["language"], "es-ES")
        request = ep.parse(
            "To: gettor@torproject.org\n"
            "From: Cecylia Bocovich <cohosh@torproject.org>\n"
            "Subject: linux fa\n"
            "Message-ID: <0befc58c-c94d-c262-9597-4365122c04b4@torproject.org>\n"
            "Date: Mon, 11 Jan 2021 11:28:37 -0500\n"
            "MIME-Version: 1.0\n"
            "Content-Type: text/plain; charset=utf-8\n"
            "Content-Language: en-US\n"
            "Content-Transfer-Encoding: 7bit\n"
            "\n"
            "linux fa\n"
        )
        self.assertEqual(request["language"], "fa")
        del ep

    @pytest_twisted.inlineCallbacks
    def test_sent_links_message(self):
        ep = self.sm_client
        links = yield ep.conn.get_links(
            platform="osx", language="en-US", status="ACTIVE"
        )
        link_msg, file = ep.build_link_strings(links, "osx", "en-US")
        body_msg = ep.build_body_message(link_msg, "osx", file)
        assert "You requested Tor Browser for osx" in body_msg

        links = yield ep.conn.get_links(
            platform="windows", language="en-US", status="ACTIVE"
        )
        link_msg, file = ep.build_link_strings(links, "windows", "en-US")
        body_msg = ep.build_body_message(link_msg, "windows", file)
        assert "You requested Tor Browser for windows" in body_msg

        links = yield ep.conn.get_links(
            platform="linux", language="en-US", status="ACTIVE"
        )
        link_msg, file = ep.build_link_strings(links, "linux", "en-US")
        body_msg = ep.build_body_message(link_msg, "linux", file)
        assert "You requested Tor Browser for linux" in body_msg

    @pytest_twisted.inlineCallbacks
    def test_help_body_message(self):
        ep = self.sm_client
        locales = yield ep.conn.get_locales()
        locale_string = ep.build_locale_string(locales)
        help_msg = ep.build_help_body_message(locale_string)
        assert "This is an automated email response from GetTor." in help_msg
        assert "\twindows\n\tlinux\n\tosx\n" in help_msg

    @pytest_twisted.inlineCallbacks
    def test_get_locales(self):
        ep = conftests.EmailParser(self.settings, "gettor@torproject.org")
        yield ep.get_locales().addErrback(ep.parse_errback)
        assert "en-US" in ep.locales
        del ep

    def test_help_reply(self):
        #Replying to GetTor Help with a valid links request should get you links
        ep = conftests.EmailParser(self.settings, "gettor@torproject.org")
        ep.locales = ["en-US", "es-ES", "es-AR", "pt-BR", "fa", "fr"]
        request = ep.parse("From: \"silvia [hiro]\" <hiro@torproject.org>\n"
                "Subject: Re: [GetTor] Help Email\r\n Reply-To: hiro@torproject.org \nTo:"
                "gettor@torproject.org\r\n\r\n osx en\n")
        self.assertEqual(request["command"], "links")
        self.assertEqual(request["language"], "en-US")
        self.assertEqual(request["platform"], "osx")

        request = ep.parse("From: \"silvia [hiro]\" <hiro@torproject.org>\n"
                "Subject: Re: [GetTor] Help Email\r\n Reply-To: hiro@torproject.org \nTo:"
                "gettor@torproject.org\r\n\r\n i like french fries\n")
        self.assertEqual(request["command"], "help")

        request = ep.parse("From: \"silvia [hiro]\" <hiro@torproject.org>\n"
                "Subject: Re: [GetTor] Help Email\r\n Reply-To: hiro@torproject.org \nTo:"
                "gettor@torproject.org\r\n\r\nlinux fa\n"
                "On 2020-02-10 11:54 a.m., gettor@torproject.org wrote:\n"
                "> This is how you can request a tor browser bundle link.\n"
                ">\n"
                "> Send an email to: gettor@torproject.org\n"
                ">\n"
                "> In the body of the email only write: <operating system> <language>.\n"
                ">\n"
                "> We only support windows, osx and linux as operating systems.\n"
                ">\n"
        )
        self.assertEqual(request["command"], "links")
        self.assertEqual(request["language"], "fa")
        self.assertEqual(request["platform"], "linux")

        request = ep.parse("From: \"silvia [hiro]\" <hiro@torproject.org>\n"
                "Subject: Re: [GetTor] Help Email\r\n Reply-To: hiro@torproject.org \nTo:"
                "gettor@torproject.org\r\n\r\nlinux fa\n"
                "On 2020-02-10 11:54 a.m., gettor@torproject.org wrote:\n"
                "This is how you can request a tor browser bundle link.\n"
                "\n"
                "Send an email to: gettor@torproject.org\n"
                "\n"
                "In the body of the email only write: <operating system> <language>.\n"
                "\n"
                "We only support windows, osx and linux as operating systems.\n"
                "\n")
        self.assertEqual(request["command"], "links")
        self.assertEqual(request["language"], "fa")
        self.assertEqual(request["platform"], "linux")

        request = ep.parse("From: \"silvia [hiro]\" <hiro@torproject.org>\n"
                "Subject: Re: [GetTor] Help Email\r\n Reply-To: hiro@torproject.org \nTo:"
                "gettor@torproject.org\r\n\r\n"
                "On 2020-02-10 11:54 a.m., gettor@torproject.org wrote:\n"
                "> This is how you can request a tor browser bundle link.\n"
                ">\n"
                "> Send an email to: gettor@torproject.org\n"
                ">\n"
                "> In the body of the email only write: <operating system> <language>.\n"
                ">\n"
                "> We only support windows, osx and linux as operating systems.\n"
                ">\n"
                "linux fa\n\n")
        self.assertEqual(request["command"], "links")
        self.assertEqual(request["language"], "fa")
        self.assertEqual(request["platform"], "linux")

        request = ep.parse("From: \"silvia [hiro]\" <hiro@torproject.org>\n"
                "Subject: Re: [GetTor] Help Email\r\n Reply-To: hiro@torproject.org \nTo:"
                "gettor@torproject.org\r\n\r\n"
                "On 2020-02-10 11:54 a.m., gettor@torproject.org wrote:\n"
                "> This is how you can request a tor browser bundle link.\n"
                ">\n"
                "> Send an email to: gettor@torproject.org\n"
                ">\n"
                "> In the body of the email only write: <operating system> <language>.\n"
                ">\n"
                "> We only support windows, osx and linux as operating systems.\n"
                ">\n")
        self.assertEqual(request["command"], "help")

    def test_from_autoresponder(self):
        ep = conftests.EmailParser(self.settings, "gettor@torproject.org")
        request = ep.parse("From: MAILER-DAEMON@mx1.riseup.net\n"
                "Subject: Undelivered Mail Returned to Sender\r\n"
                "To: gettor@torproject.org\r\n\r\n osx en\n")

        self.assertEqual(request, {})
        request = ep.parse("From: postmaster@example.sk\n"
                "Subject: Undelivered Mail Returned to Sender\r\n"
                "To: gettor@torproject.org\r\n\r\n osx en\n")

        self.assertEqual(request, {})
        request = ep.parse("From: gettor@torproject.org\n"
                "Subject: links\r\n"
                "To: gettor@torproject.org\r\n\r\n osx en\n")

        self.assertEqual(request, {})
        request = ep.parse("From: gettor+en@torproject.org\n"
                "Subject: links\r\n"
                "To: gettor@torproject.org\r\n\r\n osx en\n")

        self.assertEqual(request, {})

if __name__ == "__main__":
    unittest.main()
