#!/usr/bin/env python3
import pytest
from twisted.trial import unittest
from twisted.internet import defer, reactor
from twisted.internet import task

from . import conftests

class LocalesTests(unittest.TestCase):

    # Fail any tests which take longer than 15 seconds.
    timeout = 15
    def setUp(self):
        self.settings = conftests.options.parse_settings("en","./gettor.conf.json")
        self.locales = conftests.strings.get_locales()


    def tearDown(self):
        print("tearDown()")

    def test_load_en_strings(self):
        conftests.strings.load_strings("en")
        self.assertEqual(conftests.strings._("smtp_mirrors_subject"), "[GetTor] Mirrors")

    def test_load_default_strings(self):
        conftests.strings.load_strings(None)
        self.assertEqual(conftests.strings._("smtp_mirrors_subject"), "[GetTor] Mirrors")

    def test_load_es_strings(self):
        conftests.strings.load_strings("es")
        self.assertEqual(conftests.strings._("smtp_help_subject"), "[GetTor] Ayuda")

    def test_locale_supported(self):
        self.assertEqual(self.locales['en']['language'], "English")
        self.assertEqual(self.locales['es']['locale'], "es-ES")

if __name__ == "__main__":
    unittest.main()
