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

import json
import locale
import os
import inspect

strings = {}
translations = {}

_rundir = None

def setRundir(path):
    """Set the absolute path to the runtime directory.

    See :meth:`BaseOptions.postOptions`.

    :param string path: The path to set.
    """
    global _rundir
    _rundir = path

def getRundir():
    """Get the absolute path to the runtime directory.

    :rtype: string
    :returns: The path to the config file.
    """
    return _rundir

def find_run_dir(rundir=None):
    """Get the absolute path to the runtime directory.

    :rtype: string
    :returns: The path to the config file.
    """
    gRundir = getRundir()

    if gRundir is None:
        if rundir is not None:
            gRundir = os.path.abspath(os.path.expanduser(rundir))
        else:
            gRundir = os.getcwd()
    setRundir(gRundir)

    if not os.path.isdir(gRundir):  # pragma: no cover
        raise usage.UsageError(
            "Could not change to runtime directory: `%s'" % gRundir)

    return gRundir

def get_resource_path(filename, path):
    """
    Returns the absolute path of a resource
    """
    rundir = find_run_dir()
    prefix = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))), path)
    prefix = os.path.join(rundir, prefix)
    if not os.path.exists(prefix):
        prefix = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(prefix)))), path)

    return os.path.join(prefix, filename)

def get_version():
    # The current version
    version = ""
    with open(get_resource_path('version.txt', '../share')) as f:
        version = f.read().strip()
    return version

def get_locales():
    filename = get_resource_path("available_locales.json", '../share/locale')
    locales = {}
    with open(filename, encoding='utf-8') as f:
        locales = json.load(f)
    return locales

def load_strings(current_locale):
    """
    Loads translated strings and fallback to English
    if the translation does not exist.
    """
    global strings, translations

    # Load all translations
    translations = {}
    available_locales = get_locales()

    for locale in available_locales:

        filename = get_resource_path("{}.json".format(locale), '../share/locale')
        with open(filename, encoding='utf-8') as f:
            translations[locale] = json.load(f)

    # Build strings
    default_locale = 'en'

    strings = {}
    for s in translations[default_locale]:
        if s in translations[current_locale] and translations[current_locale][s] != "":
            strings[s] = translations[current_locale][s]
        else:
            strings[s] = translations[default_locale][s]


def translated(k):
    """
    Returns a translated string.
    """
    return strings[k]

_ = translated
