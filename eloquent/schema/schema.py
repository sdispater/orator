# -*- coding: utf-8 -*-


class Schema(object):

    def __init__(self, manager):
        """
        :param manager: The database manager
        :type manager: eloquent.DatabaseManager
        """
        self.db = manager

    def connection(self, connection=None):
        """
        Get a schema builder instance for a connection.

        :param connection: The connection to user
        :type connection: str

        :rtype: eloquent.schema.SchemaBuilder
        """
        return self.db.connection(connection).get_schema_builder()

    def __getattr__(self, item):
        return getattr(self.db.connection().get_schema_builder(), item)
