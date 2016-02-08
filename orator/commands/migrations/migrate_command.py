# -*- coding: utf-8 -*-

from orator.migrations import Migrator, DatabaseMigrationRepository
from .base_command import BaseCommand


class MigrateCommand(BaseCommand):
    """
    Run the database migrations.

    migrate
        {--d|database= : The database connection to use.}
        {--p|path= : The path of migrations files to be executed.}
        {--s|seed : Indicates if the seed task should be re-run.}
        {--seed-path= : The path of seeds files to be executed.
                        Defaults to <comment>./seeders</comment>.}
        {--P|pretend : Dump the SQL queries that would be run.}
    """

    def handle(self):
        confirm = self.confirm(
            '<question>Are you sure you want to proceed with the migration?</question> ',
            False
        )
        if not confirm:
            return

        database = self.option('database')
        repository = DatabaseMigrationRepository(self.resolver, 'migrations')

        migrator = Migrator(repository, self.resolver)

        self._prepare_database(migrator, database)

        pretend = self.option('pretend')

        path = self.option('path')

        if path is None:
            path = self._get_migration_path()

        migrator.run(path, pretend)

        for note in migrator.get_notes():
            self.line(note)

        # If the "seed" option has been given, we will rerun the database seed task
        # to repopulate the database.
        if self.option('seed'):
            options = [
                ('-n', True)
            ]

            if database:
                options.append(('--database', database))

            if self.get_definition().has_option('config'):
                options.append(('--config', self.option('config')))

            if self.option('seed-path'):
                options.append(('--path', self.option('seed-path')))

            self.call('db:seed', options)

    def _prepare_database(self, migrator, database):
        migrator.set_connection(database)

        if not migrator.repository_exists():
            options = []

            if database:
                options.append(('--database', database))

            if self.get_definition().has_option('config'):
                options.append(('--config', self.option('config')))

            self.call('migrate:install', options)
