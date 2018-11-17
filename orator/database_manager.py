# -*- coding: utf-8 -*-

import threading
import logging
from .connections.connection_resolver_interface import ConnectionResolverInterface
from .connectors.connection_factory import ConnectionFactory
from .exceptions import ArgumentError

logger = logging.getLogger("orator.database_manager")


class BaseDatabaseManager(ConnectionResolverInterface):
    def __init__(self, config, factory=ConnectionFactory()):
        """
        :param config: The connections configuration
        :type config: dict

        :param factory: A connection factory
        :type factory: ConnectionFactory
        """
        self._config = config
        self._factory = factory

        self._connections = {}

        self._extensions = {}

    def connection(self, name=None):
        """
        Get a database connection instance

        :param name: The connection name
        :type name: str

        :return: A Connection instance
        :rtype: orator.connections.connection.Connection
        """
        name, type = self._parse_connection_name(name)

        if name not in self._connections:
            logger.debug("Initiating connection %s" % name)
            connection = self._make_connection(name)

            self._set_connection_for_type(connection, type)

            self._connections[name] = self._prepare(connection)

        return self._connections[name]

    def _parse_connection_name(self, name):
        """
        Parse the connection into a tuple of the name and read / write type

        :param name: The name of the connection
        :type name: str

        :return: A tuple of the name and read / write type
        :rtype: tuple
        """
        if name is None:
            name = self.get_default_connection()

        if name.endswith(("::read", "::write")):
            return name.split("::", 1)

        return name, None

    def purge(self, name=None):
        """
        Disconnect from the given database and remove from local cache

        :param name: The name of the connection
        :type name: str

        :rtype: None
        """
        if name is None:
            name = self.get_default_connection()

        self.disconnect(name)

        if name in self._connections:
            del self._connections[name]

    def disconnect(self, name=None):
        if name is None:
            name = self.get_default_connection()

        logger.debug("Disconnecting %s" % name)

        if name in self._connections:
            self._connections[name].disconnect()

    def reconnect(self, name=None):
        if name is None:
            name = self.get_default_connection()

        logger.debug("Reconnecting %s" % name)

        self.disconnect(name)

        if name not in self._connections:
            return self.connection(name)

        return self._refresh_api_connections(name)

    def _refresh_api_connections(self, name):
        logger.debug("Refreshing api connections for %s" % name)

        fresh = self._make_connection(name)

        return (
            self._connections[name]
            .set_connection(fresh.get_connection())
            .set_read_connection(fresh.get_read_connection())
        )

    def _make_connection(self, name):
        logger.debug("Making connection for %s" % name)

        config = self._get_config(name)
        if "name" not in config:
            config["name"] = name

        if name in self._extensions:
            return self._extensions[name](config, name)

        driver = config["driver"]

        if driver in self._extensions:
            return self._extensions[driver](config, name)

        return self._factory.make(config, name)

    def _prepare(self, connection):
        logger.debug("Preparing connection %s" % connection.get_name())

        def reconnector(connection_):
            self.reconnect(connection_.get_name())

        connection.set_reconnector(reconnector)

        return connection

    def _set_connection_for_type(self, connection, type):
        if type == "read":
            connection.set_connection(connection.get_read_api())
        elif type == "write":
            connection.set_read_connection(connection.get_api())

        return connection

    def _get_config(self, name):
        if name is None:
            name = self.get_default_connection()

        connections = self._config

        config = connections.get(name)
        if not config:
            raise ArgumentError("Database [%s] not configured" % name)

        return config

    def get_default_connection(self):
        if len(self._config) == 1:
            return list(self._config.keys())[0]

        return self._config["default"]

    def set_default_connection(self, name):
        if name is not None:
            self._config["default"] = name

    def extend(self, name, resolver):
        self._extensions[name] = resolver

    def get_connections(self):
        return self._connections

    def __getattr__(self, item):
        return getattr(self.connection(), item)


class DatabaseManager(BaseDatabaseManager, threading.local):

    pass
