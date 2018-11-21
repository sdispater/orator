# -*- coding: utf-8 -*-

from orator.migrations import Migrator, DatabaseMigrationRepository
from .base_command import BaseCommand


class RollbackCommand(BaseCommand):
    """
    Rollback the last database migration.

    migrate:rollback
        {--d|database= : The database connection to use.}
        {--p|path= : The path of migrations files to be executed.}
        {--P|pretend : Dump the SQL queries that would be run.}
        {--f|force : Force the operation to run.}
    """

    def handle(self):
        """
        Executes the command.
        """
        if not self.confirm_to_proceed(
            "<question>Are you sure you want to rollback the last migration?:</question> "
        ):
            return

        database = self.option("database")
        repository = DatabaseMigrationRepository(self.resolver, "migrations")

        migrator = Migrator(repository, self.resolver)

        self._prepare_database(migrator, database)

        pretend = self.option("pretend")

        path = self.option("path")

        if path is None:
            path = self._get_migration_path()

        migrator.rollback(path, pretend)

        for note in migrator.get_notes():
            self.line(note)

    def _prepare_database(self, migrator, database):
        migrator.set_connection(database)
