# -*- coding: utf-8 -*-

import os
import glob
import inflection
import logging
from ..utils import decode


class MigratorHandler(logging.NullHandler):

    def __init__(self, level=logging.DEBUG):
        super(MigratorHandler, self).__init__(level)

        self.queries = []

    def handle(self, record):
        self.queries.append(record.query)


class Migrator(object):

    def __init__(self, repository, resolver):
        """
        :type repository: DatabaseMigrationRepository
        :type resolver: orator.database_manager.DatabaseManager
        """
        self._repository = repository
        self._resolver = resolver
        self._connection = None
        self._notes = []

    def run(self, path, pretend=False):
        """
        Run the outstanding migrations for a given path.

        :param path: The path
        :type path: str
        :param pretend: Whether we execute the migrations as dry-run
        :type pretend: bool
        """
        self._notes = []

        files = self._get_migration_files(path)

        ran = self._repository.get_ran()

        migrations = [f for f in files if f not in ran]

        self.run_migration_list(path, migrations, pretend)

    def run_migration_list(self, path, migrations, pretend=False):
        """
        Run a list of migrations.

        :type migrations: list

        :type pretend: bool
        """
        if not migrations:
            self._note('<info>Nothing to migrate</info>')

            return

        batch = self._repository.get_next_batch_number()

        for f in migrations:
            self._run_up(path, f, batch, pretend)

    def _run_up(self, path, migration_file, batch, pretend=False):
        """
        Run "up" a migration instance.

        :type migration_file: str

        :type batch: int

        :type pretend: bool
        """
        migration = self._resolve(path, migration_file)

        if pretend:
            return self._pretend_to_run(migration, 'up')

        migration.up()

        self._repository.log(migration_file, batch)

        self._note(decode('<info>✓ Migrated</info> ') + '<fg=cyan>%s</>' % migration_file)

    def rollback(self, path, pretend=False):
        """
        Rollback the last migration operation.

        :param path: The path
        :type path: str

        :param pretend: Whether we execute the migrations as dry-run
        :type pretend: bool

        :rtype: int
        """
        self._notes = []

        migrations = self._repository.get_last()

        if not migrations:
            self._note('<info>Nothing to rollback.</info>')

            return len(migrations)

        for migration in migrations:
            self._run_down(path, migration, pretend)

        return len(migrations)

    def _run_down(self, path, migration, pretend=False):
        """
        Run "down" a migration instance.
        """
        migration_file = migration['migration']

        instance = self._resolve(path, migration_file)

        if pretend:
            return self._pretend_to_run(instance, 'down')

        instance.down()

        self._repository.delete(migration)

        self._note(decode('<info>✓ Rolled back</info> ') + '<fg=cyan>%s</>' % migration_file)

    def _get_migration_files(self, path):
        """
        Get all of the migration files in a given path.

        :type path: str

        :rtype: list
        """
        files = glob.glob(os.path.join(path, '*_*.py'))

        if not files:
            return []

        files = list(map(lambda f: os.path.basename(f).replace('.py', ''), files))

        files = sorted(files)

        return files

    def _pretend_to_run(self, migration, method):
        """
        Pretend to run the migration.

        :param migration: The migration
        :type migration: orator.migrations.migration.Migration

        :param method: The method to execute
        :type method: str
        """
        for query in self._get_queries(migration, method):
            name = migration.__class__.__name__

            self._note('<info>%s:</info> <comment>%s</comment>' % (name, query))

    def _get_queries(self, migration, method):
        """
        Get all of the queries that would be run for a migration.

        :param migration: The migration
        :type migration: orator.migrations.migration.Migration

        :param method: The method to execute
        :type method: str

        :rtype: list
        """
        connection = migration.get_connection()

        db = self.resolve_connection(connection)

        logger = logging.getLogger('orator.connection.queries')
        level = logger.level
        logger.setLevel(logging.DEBUG)
        handler = MigratorHandler()
        handler.setLevel(logging.DEBUG)
        logger.addHandler(handler)

        db.pretend(lambda _: getattr(migration, method)())

        logger.removeHandler(handler)
        logger.setLevel(level)

        return handler.queries

    def _resolve(self, path, migration_file):
        """
        Resolve a migration instance from a file.

        :param migration_file: The migration file
        :type migration_file: str

        :rtype: orator.migrations.migration.Migration
        """
        variables = {}

        name = '_'.join(migration_file.split('_')[4:])
        migration_file = os.path.join(path, '%s.py' % migration_file)

        with open(migration_file) as fh:
            exec(fh.read(), {}, variables)

        klass = variables[inflection.camelize(name)]

        instance = klass()
        instance.set_schema_builder(self.get_repository().get_connection().get_schema_builder())

        return instance

    def _note(self, message):
        """
        Add a note to the migrator.

        :param message: The message
        :type message: str
        """
        self._notes.append(message)

    def resolve_connection(self, connection):
        return self._resolver.connection(connection)

    def set_connection(self, name):
        if name is not None:
            self._resolver.set_default_connection(name)

        self._repository.set_source(name)

        self._connection = name

    def get_repository(self):
        return self._repository

    def repository_exists(self):
        return self._repository.repository_exists()

    def get_notes(self):
        return self._notes
