# -*- coding: utf-8 -*-

from orator.migrations import Migrator, DatabaseMigrationRepository
from .base_command import BaseCommand


class MigrateCommand(BaseCommand):

    name = 'migrations:run'

    aliases = ['migrate']

    description = 'Run the database migrations.'

    options = [{
        'name': 'database',
        'shortcut': 'd',
        'description': 'The database connection to use.',
        'value_required': True
    }, {
        'name': 'path',
        'shortcut': 'p',
        'description': 'The path of migrations files to be executed.',
        'value_required': True
    }, {
        'name': 'seed',
        'shortcut': 's',
        'description': 'Indicates if the seed task should be re-run.',
        'flag': True
    }, {
        'name': 'seed-path',
        'description': 'The path of seeds files to be executed. '
                       'Defaults to <comment>./seeders</comment>',
        'value_required': True
    }, {
        'name': 'pretend',
        'shortcut': 'P',
        'description': 'Dump the SQL queries that would be run.',
        'flag': True
    }]

    def fire(self):
        """
        Executes the command.
        """
        dialog = self.get_helper('dialog')
        confirm = dialog.ask_confirmation(
            self.output,
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
                ('--database', database),
                ('-n', True)
            ]

            if self.get_definition().has_option('config'):
                options.append(('--config', self.option('config')))

            if self.option('seed-path'):
                options.append(('--path', self.option('seed-path')))

            self.call('db:seed', options)

    def _prepare_database(self, migrator, database):
        migrator.set_connection(database)

        if not migrator.repository_exists():
            options = [
                ('--database', database)
            ]

            if self.get_definition().has_option('config'):
                options.append(('--config', self.input.get_option('config')))

            self.call('migrations:install', options)
