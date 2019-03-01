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

	"""
	def __init__(self, dbname):
		"""Constructor."""
		self.dbpool = adbapi.ConnectionPool(
			"sqlite3", dbname, check_same_thread=False
		)

	def query_callback(self, results=None):
		""" """
		log.msg("Database query executed successfully.")
		return results

	def query_errback(self, error=None):
		""" """
		if error:
			log.msg("Database error: {}".format(error))
		return None

	def new_request(self, id, command, service, platform, date, status):
		""" """
		query = "INSERT INTO requests VALUES(?, ?, ?, ?, ?, ?)"

		return self.dbpool.runQuery(
			query, (id, command, platform, service, date, status)
		).addCallback(self.query_callback).addErrback(self.query_errback)

	def get_requests(self, status, command, service):
		""" """
		query = "SELECT * FROM requests WHERE service=? AND command=? AND "\
		"status = ?"

		return self.dbpool.runQuery(
			query, (service, command, status)
		).addCallback(self.query_callback).addErrback(self.query_errback)

	def get_num_requests(self, id, service):
		""" """
		query = "SELECT COUNT(rowid) FROM requests WHERE id=? AND service=?"

		return self.dbpool.runQuery(
			query, (id, service)
		).addCallback(self.query_callback).addErrback(self.query_errback)

	def update_request(self, id, hid, status, service, date):
		""" """
		query = "UPDATE requests SET id=?, status=? WHERE id=? AND "\
		"service=? AND date=?"

		return self.dbpool.runQuery(
			query, (hid, status, id, service, date)
		).addCallback(self.query_callback).addErrback(self.query_errback)

	def update_stats(self, command, service, platform=None):
		""" """
		now_str = datetime.now().strftime("%Y%m%d")
		query = "REPLACE INTO stats(num_requests, platform, "\
		"command, service, date) VALUES(COALESCE((SELECT num_requests FROM stats "\
		"WHERE date=?)+1, 0), ?, ?, ?, ?) "\

		return self.dbpool.runQuery(
			query, (now_str,platform, command, service, now_str)
		).addCallback(self.query_callback).addErrback(self.query_errback)

	def get_links(self, platform, status):
		""" """
		query = "SELECT * FROM links WHERE platform=? AND status=?"
		return self.dbpool.runQuery(
			query, (platform, status)
		).addCallback(self.query_callback).addErrback(self.query_errback)
