# -*- coding: utf-8 -*-

from .base_command import BaseCommand


class RefreshCommand(BaseCommand):
    """
    Reset and re-run all migrations.

    migrate:refresh
        {--d|database= : The database connection to use.}
        {--p|path= : The path of migrations files to be executed.}
        {--s|seed : Indicates if the seed task should be re-run.}
        {--seed-path= : The path of seeds files to be executed.
                        Defaults to <comment>./seeders</comment>.}
        {--seeder=database_seeder : The name of the root seeder.}
    """

    def handle(self):
        """
        Executes the command.
        """
        confirm = self.confirm(
            '<question>Are you sure you want to refresh the database?</question> ',
            False
        )
        if not confirm:
            return

        database = self.option('database')

        options = [
            ('-n', True)
        ]

        if self.option('path'):
            options.append(('--path', self.option('path')))

        if database:
            options.append(('--database', database))

        if self.get_definition().has_option('config'):
            options.append(('--config', self.option('config')))

        self.call('migrate:reset', options)

        self.call('migrate', options)

        if self._needs_seeding():
            self._run_seeder(database)

    def _needs_seeding(self):
        return self.option('seed') or self.option('seeder')

    def _run_seeder(self, database):
        options = [
            ('--seeder', self.option('seeder')),
            ('-n', True)
        ]

        if database:
            options.append(('--database', database))

        if self.get_definition().has_option('config'):
            options.append(('--config', self.option('config')))

        if self.option('seed-path'):
            options.append(('--path', self.option('seed-path')))

        self.call('db:seed', options)
