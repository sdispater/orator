# -*- coding: utf-8 -*-

from orator.migrations import Migrator, DatabaseMigrationRepository
from .base_command import BaseCommand


class StatusCommand(BaseCommand):
    """
    Show a list of migrations up/down.

    migrate:status
        {--d|database= : The database connection to use.}
        {--p|path= : The path of migrations files to be executed.}
    """

    def handle(self):
        """
        Executes the command.
        """
        database = self.option("database")

        self.resolver.set_default_connection(database)

        repository = DatabaseMigrationRepository(self.resolver, "migrations")

        migrator = Migrator(repository, self.resolver)

        if not migrator.repository_exists():
            return self.error("No migrations found")

        self._prepare_database(migrator, database)

        path = self.option("path")

        if path is None:
            path = self._get_migration_path()

        ran = migrator.get_repository().get_ran()

        migrations = []
        for migration in migrator._get_migration_files(path):
            if migration in ran:
                migrations.append(["<fg=cyan>%s</>" % migration, "<info>Yes</>"])
            else:
                migrations.append(["<fg=cyan>%s</>" % migration, "<fg=red>No</>"])

        if migrations:
            table = self.table(["Migration", "Ran?"], migrations)
            table.render()
        else:
            return self.error("No migrations found")

        for note in migrator.get_notes():
            self.line(note)

    def _prepare_database(self, migrator, database):
        migrator.set_connection(database)
