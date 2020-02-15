#!/usr/bin/env python3
"""
This file is part of GetTor, a service providing alternative methods to download
the Tor Browser.

:authors: Hiro <hiro@torproject.org>
          Cecylia Bocovich <cohosh@torproject.org>
          please also see AUTHORS file
:copyright: (c) 2008-2020, The Tor Project, Inc.
            (c) 2020, all entities within the AUTHORS file
:license: see included LICENSE for information
"""
import setuptools

setuptools.setup(
        name='gettor',
        version='0.0.1',
        description='Backend system for distributing Tor Browser downloads',
        author='Israel Leiva',
        author_email='ilv@torproject.org',
        maintainer='Cecylia Bocovich',
        maintainer_email='cohosh@torproject.org',
        url='https://gettor.torproject.org',
        download_url='https://gitweb.torproject.org/gettor.git',
        package_dir={'gettor': 'gettor'},
        packages=setuptools.find_packages(),
        scripts=['scripts/add_links_to_db',
                 'scripts/create_db',
                 'scripts/export_stats',
                 'scripts/process_email',
                 'scripts/update_files',
                 'scripts/update_git'],
        install_requires=['twisted',
                          'pytest',
                          'requests_oauthlib',
                          'dkimpy'],
)

