# -*- coding: utf-8 -*-

import os
from cleo import InputOption, ListInput
from orator.migrations import Migrator, DatabaseMigrationRepository
from .base_command import BaseCommand


class RefreshCommand(BaseCommand):

    def configure(self):
        super(RefreshCommand, self).configure()

        self.set_name('migrations:refresh')
        self.set_description('Reset and re-run all migrations')
        self.add_option('database', 'd', InputOption.VALUE_OPTIONAL,
                        'The database connection to use')
        self.add_option('path', 'p', InputOption.VALUE_OPTIONAL,
                        'The path of migrations files to be executed.')
        self.add_option('seed', 's', InputOption.VALUE_NONE,
                        'Indicates if the seed task should be re-run.')
        self.add_option('seeder', None, InputOption.VALUE_REQUIRED,
                        'The name of the root seeder.',
                        default='database_seeder')
        self.add_option('seed-path', None, InputOption.VALUE_REQUIRED,
                        'The path of seeds files to be executed. '
                        'Defaults to <comment>./seeders</comment>')

    def execute(self, i, o):
        """
        Executes the command.

        :type i: cleo.inputs.input.Input
        :type o: cleo.outputs.output.Output
        """
        super(RefreshCommand, self).execute(i, o)

        dialog = self.get_helper('dialog')
        confirm = dialog.ask_confirmation(
            o,
            '<question>Are you sure you want to refresh the database?</question> ',
            False
        )
        if not confirm:
            return

        database = i.get_option('database')

        self.call(
            'migrations:reset',
            [
                ('--database', database),
                ('--config', i.get_option('config')),
                ('--path', i.get_option('path')),
                ('-n', True)
            ],
            o
        )

        self.call(
            'migrations:run',
            [
                ('--database', database),
                ('--config', i.get_option('config')),
                ('--path', i.get_option('path')),
                ('-n', True)
            ],
            o
        )

        if self._needs_seeding(i):
            self._run_seeder(i, database, o)

    def _needs_seeding(self, i):
        return i.get_option('seed') or i.get_option('seeder')

    def _run_seeder(self, i, database, o):
        options = [
            ('--database', database),
            ('--config', i.get_option('config')),
            ('--seeder', i.get_option('seeder')),
            ('-n', True)
        ]
        if i.get_option('seed-path'):
            options.append(('--path', i.get_option('seed-path')))

        self.call('db:seed', options, o)
