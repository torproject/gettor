# -*- coding: utf-8 -*-
"""
This file is part of GetTor, a service providing alternative methods to download
the Tor Browser.

:authors: Hiro <hiro@torproject.org> please also see AUTHORS file
:copyright: (c) 2008-2014, The Tor Project, Inc.
            (c) 2014, all entities within the AUTHORS file
:license: see included LICENSE for information
"""

from .settings import Settings
from . import strings

def load_settings(config):
    """
    Loading settings, optionally from a custom config json file.
    """
    settings = Settings(config)
    settings.load()
    return settings

def parse_settings(locale="en", config=None):
    """
    Parse settings and loads strings in a given locale
    This function needs to be rewritten considering passing a locale and
    returing translated strings

    """

    strings.load_strings(locale)
    return load_settings(config)
