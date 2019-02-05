# -*- coding: utf-8 -*-
"""
This file is part of GetTor, a service providing alternative methods to download
the Tor Browser.

:authors: Hiro <hiro@torproject.org>
          please also see AUTHORS file
:copyright: (c) 2008-2014, The Tor Project, Inc.
            (c) 2014, all entities within the AUTHORS file
:license: see included LICENSE for information
"""

from __future__ import print_function
from .gettor.utils import options

class EmailServiceTests(unittest.TestCase):

    # Fail any tests which take longer than 15 seconds.
    timeout = 15
    def setUp(self):
        self.setings = options.parse_settings()

    def test_SendMail(self):
        sendmail = Sendmail(self.settings)
        mail = Sendmail.sendmail("gettor@torproject.org", "Hello", "This is a test.")
        print(email)
        self.assertEqual(mail, True)
