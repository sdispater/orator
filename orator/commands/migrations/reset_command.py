# -*- coding: utf-8 -*-

from orator.migrations import Migrator, DatabaseMigrationRepository
from .base_command import BaseCommand


class ResetCommand(BaseCommand):
    """
    Rollback all database migrations.

    migrate:reset
        {--d|database= : The database connection to use.}
        {--p|path= : The path of migrations files to be executed.}
        {--P|pretend : Dump the SQL queries that would be run.}
    """

    def handle(self):
        """
        Executes the command.
        """
        confirm = self.confirm(
            '<question>Are you sure you want to reset all of the migrations?</question> ',
            False
        )
        if not confirm:
            return

        database = self.option('database')
        repository = DatabaseMigrationRepository(self.resolver, 'migrations')

        migrator = Migrator(repository, self.resolver)

        self._prepare_database(migrator, database)

        pretend = bool(self.option('pretend'))

        path = self.option('path')

        if path is None:
            path = self._get_migration_path()

        migrator.reset(path, pretend)

        for note in migrator.get_notes():
            self.line(note)

    def _prepare_database(self, migrator, database):
        migrator.set_connection(database)
