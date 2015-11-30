# -*- coding: utf-8 -*-

from .base_command import BaseCommand


class RefreshCommand(BaseCommand):

    name = 'migrations:refresh'

    description = 'Reset and re-run all migrations.'

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
        'name': 'seeder',
        'description': 'The name of the root seeder.',
        'value_required': True,
        'default': 'database_seeder'
    }]

    def fire(self):
        """
        Executes the command.
        """
        dialog = self.get_helper('dialog')
        confirm = dialog.ask_confirmation(
            self.output,
            '<question>Are you sure you want to refresh the database?</question> ',
            False
        )
        if not confirm:
            return

        database = self.option('database')

        options = [
            ('--database', database),
            ('--path', self.option('path')),
            ('-n', True)
        ]
        if self.get_definition().has_option('config'):
            options.append(('--config', self.option('config')))

        self.call('migrations:reset', options)

        self.call('migrations:run', options)

        if self._needs_seeding():
            self._run_seeder(database)

    def _needs_seeding(self):
        return self.option('seed') or self.option('seeder')

    def _run_seeder(self, database):
        options = [
            ('--database', database),
            ('--seeder', self.option('seeder')),
            ('-n', True)
        ]

        if self.get_definition().has_option('config'):
            options.append(('--config', self.option('config')))

        if self.option('seed-path'):
            options.append(('--path', self.option('seed-path')))

        self.call('db:seed', options)
