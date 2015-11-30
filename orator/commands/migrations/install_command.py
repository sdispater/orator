# -*- coding: utf-8 -*-

from orator.migrations import DatabaseMigrationRepository
from .base_command import BaseCommand


class InstallCommand(BaseCommand):

    name = 'migrations:install'

    description = 'Create the migration repository'

    options = [{
        'name': 'database',
        'shortcut': 'd',
        'description': 'The database connection to use.',
        'value_required': True
    }]

    def fire(self):
        """
        Executes the command
        """
        database = self.option('database')
        repository = DatabaseMigrationRepository(self.resolver, 'migrations')

        repository.set_source(database)
        repository.create_repository()

        self.info('✓ Migration table created successfully')
