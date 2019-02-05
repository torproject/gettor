# -*- coding: utf-8 -*-
"""
This file is part of GetTor, a service providing alternative methods to download
the Tor Browser.

:authors: Hiro <hiro@torproject.org>
            parser = argparse.ArgumentParser(formatter_class=lambda prog: argparse.HelpFormatter(prog,max_help_position=28))
    parser.add_argument('--config', metavar='config',  please also see AUTHORS file
:copyright: (c) 2008-2014, The Tor Project, Inc.
            (c) 2014, all entities within the AUTHORS file
:license: see included LICENSE for information
"""

import argparse

from .settings import Settings
from . import strings

def load_settings(config=None):
    """
    Loading settings, optionally from a custom config json file.
    """
    settings = Settings(config)
    settings.load()
    return settings

def parse_settings():
    strings.load_strings("en")

    return load_settings(config=False)
