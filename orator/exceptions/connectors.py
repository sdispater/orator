# -*- coding: utf-8 -*-


class ConnectorException(Exception):

    pass


class UnsupportedDriver(ConnectorException):

    def __init__(self, driver):
        message = 'Driver "%s" is not supported' % driver

        super(UnsupportedDriver, self).__init__(message)
