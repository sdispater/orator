# -*- coding: utf-8 -*-

from .migration import Migration


class DatabaseMigrationRepository(object):
    def __init__(self, resolver, table):
        """
        :type resolver: orator.database_manager.DatabaseManager
        :type table: str
        """
        self._resolver = resolver
        self._table = table
        self._connection = None

    def get_ran(self):
        """
        Get the ran migrations.

        :rtype: list
        """
        return self.table().lists("migration")

    def get_last(self):
        """
        Get the last migration batch.

        :rtype: list
        """
        query = self.table().where("batch", self.get_last_batch_number())

        return query.order_by("migration", "desc").get()

    def log(self, file, batch):
        """
        Log that a migration was run.

        :type file: str
        :type batch: int
        """
        record = {"migration": file, "batch": batch}

        self.table().insert(**record)

    def delete(self, migration):
        """
        Remove a migration from the log.

        :type migration: dict
        """
        self.table().where("migration", migration["migration"]).delete()

    def get_next_batch_number(self):
        """
        Get the next migration batch number.

        :rtype: int
        """
        return self.get_last_batch_number() + 1

    def get_last_batch_number(self):
        """
        Get the last migration batch number.

        :rtype: int
        """
        return self.table().max("batch") or 0

    def create_repository(self):
        """
        Create the migration repository data store.
        """
        schema = self.get_connection().get_schema_builder()

        with schema.create(self._table) as table:
            # The migrations table is responsible for keeping track of which of the
            # migrations have actually run for the application. We'll create the
            # table to hold the migration file's path as well as the batch ID.
            table.string("migration")
            table.integer("batch")

    def repository_exists(self):
        """
        Determine if the repository exists.

        :rtype: bool
        """
        schema = self.get_connection().get_schema_builder()

        return schema.has_table(self._table)

    def table(self):
        """
        Get a query builder for the migration table.

        :rtype: orator.query.builder.QueryBuilder
        """
        return self.get_connection().table(self._table)

    def get_connection_resolver(self):
        return self._resolver

    def get_connection(self):
        return self._resolver.connection(self._connection)

    def set_source(self, name):
        self._connection = name
