# -*- coding: utf-8 -*-
#
# This file is part of GetTor, a Tor Browser distribution system.
#
# :authors: isra <ilv@torproject.org>
#           see also AUTHORS file
#
# :license: This is Free Software. See LICENSE for license information.

from __future__ import absolute_import

from datetime import datetime

from twisted.python import log
from twisted.enterprise import adbapi

class SQLite3(object):
	"""
	This class handles the database connections and operations.
	"""
	def __init__(self, dbname):
		"""Constructor."""
		self.dbpool = adbapi.ConnectionPool(
			"sqlite3", dbname, check_same_thread=False
		)

	def query_callback(self, results=None):
		"""
		Query callback
		Log that the database query has been executed and return results
		"""
		log.msg("Database query executed successfully.")
		return results

	def query_errback(self, error=None):
		"""
        Query error callback
		Logs database error
		"""
		if error:
			log.msg("Database error: {}".format(error))
		return None

	def new_request(self, id, command, service, platform, language, date, status):
		"""
		Perform a new request to the database
		"""
		query = "INSERT INTO requests VALUES(?, ?, ?, ?, ?, ?, ?)"

		return self.dbpool.runQuery(
			query, (id, command, platform, language, service, date, status)
		).addCallback(self.query_callback).addErrback(self.query_errback)

	def get_requests(self, status, command, service):
		"""
		Perform a SELECT request to the database
		"""
		query = "SELECT * FROM requests WHERE service=? AND command=? AND "\
		"status = ?"

		return self.dbpool.runQuery(
			query, (service, command, status)
		).addCallback(self.query_callback).addErrback(self.query_errback)

	def get_num_requests(self, id, service):
		"""
		Get number of requests for statistics
		"""
		query = "SELECT COUNT(rowid) FROM requests WHERE id=? AND service=?"

		return self.dbpool.runQuery(
			query, (id, service)
		).addCallback(self.query_callback).addErrback(self.query_errback)

	def update_request(self, id, hid, status, service, date):
		"""
		Update request record in the database
		"""
		query = "UPDATE requests SET id=?, status=? WHERE id=? AND "\
		"service=? AND date=?"

		return self.dbpool.runQuery(
			query, (hid, status, id, service, date)
		).addCallback(self.query_callback).addErrback(self.query_errback)

	def update_stats(self, command, service, platform=None, language='en'):
		"""
		Update statistics to the database
		"""
		now_str = datetime.now().strftime("%Y%m%d")
		query = "INSERT INTO stats(num_requests, platform, language, command, "\
		        "service, date) VALUES (1, ?, ?, ?, ?, ?) ON CONFLICT(platform, "\
				"language, command, service, date) DO UPDATE SET num_requests=num_requests+1"

		return self.dbpool.runQuery(
			query, (platform, language, command, service, now_str)
		).addCallback(self.query_callback).addErrback(self.query_errback)

	def get_links(self, platform, language, status):
		"""
		Get links from the database per platform
		"""
		query = "SELECT * FROM links WHERE platform=? AND language=? AND status=?"
		return self.dbpool.runQuery(
			query, (platform, language, status)
		).addCallback(self.query_callback).addErrback(self.query_errback)

	def get_locales(self):
		"""
		Get a list of the supported tor browser binary locales
		"""
		query = "SELECT DISTINCT language FROM links"
		return self.dbpool.runQuery(query
		).addCallback(self.query_callback).addErrback(self.query_errback)
