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
        self.locales = conftests.strings.get_locales()


    def tearDown(self):
        print("tearDown()")

    def test_get_available_locales(self):
        self.assertEqual({"en": "English", "es": "Español", "pt": "Português Brasil"}, self.locales)

    def test_load_en_strings(self):
        conftests.strings.load_strings("en")
        self.assertEqual(conftests.strings._("smtp_mirrors_subject"), "[GetTor] Mirrors")

    def test_load_es_strings(self):
        conftests.strings.load_strings("es")
        self.assertEqual(conftests.strings._("smtp_help_subject"), "[GetTor] Ayuda")

if __name__ == "__main__":
    unittest.main()
