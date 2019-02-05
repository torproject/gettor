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

"""This module sets up GetTor and starts the servers running."""

import sys

from .utils.commons import log
from .utils import options
from .services import BaseService
from .services.email.sendmail import Sendmail


def run(gettor, app):
    """
        This is GetTor's main entry point and main runtime loop.
    """
    settings = options.parse_settings()

    sendmail = Sendmail(settings)

    log.info("Starting services.")
    sendmail_service = BaseService(
        "sendmail", sendmail.get_interval(), sendmail
    )

    gettor.addService(sendmail_service)

    gettor.setServiceParent(app)
