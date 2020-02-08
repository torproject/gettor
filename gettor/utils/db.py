# -*- coding: utf-8 -*-
#
# This file is part of GetTor, a Tor Browser distribution system.
#
# :authors: isra <ilv@torproject.org>
#           see also AUTHORS file
#
# :license: This is Free Software. See LICENSE for license information.

from __future__ import absolute_import

import sqlite3
from datetime import datetime

from twisted.python import log

class SQLite3(object):
	"""
	This class handles the database connections and operations.
	"""
	def __init__(self, dbname):
		"""Constructor."""
		self.conn = sqlite3.connect(dbname)

	def new_request(self, id, command, service, platform, language, date, status):
		"""
		Perform a new request to the database
		"""
		c = self.conn.cursor()
		query = "INSERT INTO requests VALUES(?, ?, ?, ?, ?, ?, ?)"

		c.execute(query, (id, command, platform, language, service,
                    date, status))
		self.conn.commit()
		return

	def get_requests(self, status, command, service):
		"""
		Perform a SELECT request to the database
		"""
		c = self.conn.cursor()
		query = "SELECT * FROM requests WHERE service=? AND command=? AND "\
		"status = ?"

		c.execute(query, (service, command, status))

		return c.fetchall()

	def get_num_requests(self, id, service):
		"""
		Get number of requests for statistics
		"""
		c = self.conn.cursor()
		query = "SELECT COUNT(rowid) FROM requests WHERE id=? AND "\
		"service=?"

		c.execute(query, (id, service))
		return c.fetchone()[0]

	def remove_request(self, id, service, date):
		"""
		Removes completed request record from the database
		"""
		c = self.conn.cursor()
		query = "DELETE FROM requests WHERE id=? AND service=? AND "\
                "date=?"

		c.execute(query, (id, service, date))
		self.conn.commit()
		return

	def update_stats(self, command, service, platform=None, language='en'):
		"""
		Update statistics to the database
		"""
		c = self.conn.cursor()
		now_str = datetime.now().strftime("%Y%m%d")
		query = "INSERT INTO stats(num_requests, platform, language, command, "\
		        "service, date) VALUES (1, ?, ?, ?, ?, ?) ON "\
                        "CONFLICT(platform, language, command, service, date) "\
                        "DO UPDATE SET num_requests=num_requests+1"

		c.execute(query, (platform, language, command, service,
		    now_str))
		self.conn.commit()
		return

	def get_links(self, platform, language, status):
		"""
		Get links from the database per platform
		"""
		c = self.conn.cursor()
		query = "SELECT * FROM links WHERE platform=? AND language=? AND status=?"
		c.execute(query, (platform, language, status))

		return c.fetchall()

	def get_locales(self):
		"""
		Get a list of the supported tor browser binary locales
		"""
		c = self.conn.cursor()
		query = "SELECT DISTINCT language FROM links"
		c.execute(query)

		locales = []
		for locale in c.fetchall():
		    locales.append(locale[0])
		return locales
