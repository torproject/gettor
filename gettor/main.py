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

"""
This sets up GetTor and starts the servers running.
"""

from .utils.commons import log
from .utils import options

from .services import BaseService
from .services.email.sendmail import Sendmail
from .services.twitter.twitterdm import Twitterdm

def run(gettor, app):
    """
    This is GetTor's main entry point and main runtime loop.
    """
    config = "/home/gettor/gettor/gettor.conf.json"

    settings = options.parse_settings("en", config)

    sendmail = Sendmail(settings)
    twitterdm = Twitterdm(settings)

    log.info("Starting services.")
    sendmail_service = BaseService(
        "sendmail", sendmail.get_interval(), sendmail
    )

    gettor.addService(sendmail_service)

    gettor.setServiceParent(app)


    twitter_service = BaseService(
        "twitterdm", twitterdm.get_interval(), twitterdm
    )

    gettor.addService(twitter_service)

    gettor.setServiceParent(app)
