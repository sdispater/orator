# -*- coding: utf-8 -*-

from ..dbal.exceptions import InvalidPlatformSpecified
from ..exceptions.connectors import MissingPackage


class Connector(object):

    RESERVED_KEYWORDS = ["log_queries", "driver", "prefix", "name"]

    SUPPORTED_PACKAGES = []

    def __init__(self, driver=None):
        if self.get_api() is None:
            raise MissingPackage(driver, self.SUPPORTED_PACKAGES)

        self._connection = None
        self._platform = None
        self._params = {}

    def get_api(self):
        raise NotImplementedError()

    def get_config(self, config):
        default_config = self.get_default_config()
        config = {x: config[x] for x in config if x not in self.RESERVED_KEYWORDS}

        default_config.update(config)

        return default_config

    def get_default_config(self):
        return {}

    def connect(self, config):
        self._params = self.get_config(config)
        self._connection = self._do_connect(config)

        return self

    def _do_connect(self, config):
        return self.get_api().connect(**self.get_config(config))

    def get_params(self):
        return self._params

    def get_database(self):
        return self._params.get("database")

    def get_host(self):
        return self._params.get("host")

    def get_user(self):
        return self._params.get("user")

    def get_password(self):
        return self._params.get("password")

    def get_database_platform(self):
        if self._platform is None:
            self._detect_database_platform()

        return self._platform

    def _detect_database_platform(self):
        """
        Detects and sets the database platform.

        Evaluates custom platform class and version in order to set the correct platform.

        :raises InvalidPlatformSpecified: if an invalid platform was specified for this connection.
        """
        version = self._get_database_platform_version()

        if version is not None:
            self._platform = self._create_database_platform_for_version(version)
        else:
            self._platform = self.get_dbal_platform()

    def _get_database_platform_version(self):
        """
        Returns the version of the related platform if applicable.

        Returns None if either the connector is not capable to create version
        specific platform instances, no explicit server version was specified
        or the underlying driver connection cannot determine the platform
        version without having to query it (performance reasons).

        :rtype: str or None
        """
        # Connector does not support version specific platforms.
        if not self.is_version_aware():
            return None

        return self.get_server_version()

    def _create_database_platform_for_version(self, version):
        raise NotImplementedError()

    def get_dbal_platform(self):
        raise NotImplementedError()

    def is_version_aware(self):
        return True

    def get_server_version(self):
        return None

    def __getattr__(self, item):
        return getattr(self._connection, item)
