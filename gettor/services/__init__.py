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

from __future__ import absolute_import

from twisted.application import internet
from ..utils.commons import log

class BaseService(internet.TimerService):
    """
    Base service for Accounts, Messages and Fetchmail. It extends the
    TimerService providing asynchronous connection to database by default.
    """

    def __init__(self, name, step, instance, *args, **kwargs):
        """
        Constructor. Initiate connection to database and link one of Accounts,
        Messages or Fetchmail instances to TimerService behavour.

        :param name (str): name of the service being initiated (just for log
                           purposes).
        :param step (float): time interval for TimerService, in seconds.
        :param instance (object): instance of Accounts, Messages, or
                                  Fetchmail classes.
        """

        log.info("SERVICE:: Initializing {} service.".format(name))
        self.name = name
        self.instance = instance
        log.debug("SERVICE:: Initializing TimerService.")
        internet.TimerService.__init__(
            self, step, self.instance.get_new, **kwargs
        )

    def startService(self):
        """
        Starts the service. Overridden from parent class to add extra logging
        information.
        """
        log.info("SERVICE:: Starting {} service.".format(self.name))
        internet.TimerService.startService(self)
        log.info("SERVICE:: Service started.")

    def stopService(self):
        """
        Stop the service. Overridden from parent class to close connection to
        database, shutdown the service and add extra logging information.
        """
        log.info("SERVICE:: Stopping {} service.".format(self.name))
        log.debug("SERVICE:: Calling shutdown on {}".format(self.name))
        del self.instance
        log.debug("SERVICE:: Shutdown for {} done".format(self.name))
        internet.TimerService.stopService(self)
        log.info("SERVICE:: Service stopped.")
