# -*- coding: utf-8 -*-
#
# This file is part of GetTor, a Tor Browser distribution system.
#
# :authors: isra <ilv@torproject.org>
#           see also AUTHORS file
#
# :copyright:   (c) 2008-2014, The Tor Project, Inc.
#               (c) 2014-2018, Israel Leiva
#
# :license: This is Free Software. See LICENSE for license information.

from twisted.logger import Logger
from twisted.application import internet

# Define an application logger
log = Logger(namespace="gettor")

class BaseService(internet.TimerService):
    """
    Base service for Email and Sendmail. It extends the TimerService.
    """

    def __init__(self, name, step, instance, *args, **kwargs):
        """
        Constructor.

        :param name (str): name of the service (just for logging purposes).
        :param step (float): time interval for TimerService, in seconds.
        :param instance (object): instance of Email, Sendmail classes
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
        internet.TimerService.stopService(self)
        log.info("SERVICE:: Service stopped.")
