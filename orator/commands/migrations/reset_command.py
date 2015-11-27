# -*- coding: utf-8 -*-

from orator.migrations import Migrator, DatabaseMigrationRepository
from .base_command import BaseCommand


class ResetCommand(BaseCommand):

    name = 'migrations:reset'

    description = 'Rollback all database migrations.'

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

        while True:
            count = migrator.rollback(path, pretend)

            for note in migrator.get_notes():
                self.line(note)

            if count == 0:
                break

    def _prepare_database(self, migrator, database):
        migrator.set_connection(database)
