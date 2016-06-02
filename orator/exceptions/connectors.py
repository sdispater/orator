# -*- coding: utf-8 -*-


class ConnectorException(Exception):

    pass


class UnsupportedDriver(ConnectorException):

    def __init__(self, driver):
        message = 'Driver "%s" is not supported' % driver

        super(UnsupportedDriver, self).__init__(message)


class MissingPackage(ConnectorException):

    def __init__(self, driver, supported_packages):
        if not isinstance(supported_packages, list):
            supported_packages = [supported_packages]

        message = 'Driver "%s" requires ' % driver
        if len(supported_packages) == 1:
            message += '"%s" package' % supported_packages[0]
        else:
            message += 'one of the following packages: "%s"' % ('", "'.join(supported_packages))
            
        super(MissingPackage, self).__init__(message)
