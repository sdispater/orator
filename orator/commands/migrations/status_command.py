# -*- coding: utf-8 -*-

from orator.migrations import Migrator, DatabaseMigrationRepository
from .base_command import BaseCommand


class StatusCommand(BaseCommand):

    name = 'migrations:status'

    description = 'Show a list of migrations up/down'

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
    }]

    def fire(self):
        """
        Executes the command.
        """
        database = self.option('database')
        repository = DatabaseMigrationRepository(self.resolver, 'migrations')

        migrator = Migrator(repository, self.resolver)

        if not migrator.repository_exists():
            return self.error('No migrations found')

        self._prepare_database(migrator, database)

        path = self.option('path')

        if path is None:
            path = self._get_migration_path()

        ran = migrator.get_repository().get_ran()

        migrations = []
        for migration in migrator._get_migration_files(path):
            if migration in ran:
                migrations.append(['<fg=cyan>%s</>' % migration, '<info>Yes</info>'])
            else:
                migrations.append(['<fg=cyan>%s</>' % migration, '<fg=red>No</>'])

        if migrations:
            table = self.get_helper('table')
            table.set_headers(['Migration', 'Ran?'])
            table.set_rows(migrations)
            table.render(self.output)
        else:
            return self.error('No migrations found')

        for note in migrator.get_notes():
            self.line(note)

    def _prepare_database(self, migrator, database):
        migrator.set_connection(database)
