# -*- coding: utf-8 -*-

import os
from orator.migrations import MigrationCreator
from .base_command import BaseCommand


class MigrateMakeCommand(BaseCommand):

    name = 'migrations:make'

    description = 'Create a new migration file.'

    arguments = [{
        'name': 'name',
        'description': 'The name of the migration.',
        'required': True
    }]

    options = [{
        'name': 'table',
        'shortcut': 't',
        'description': 'the table to create the migration for.',
        'value_required': True
    }, {
        'name': 'create',
        'shortcut': 'C',
        'description': 'Whether the migration will create the table or not.',
        'flag': True
    }, {
        'name': 'path',
        'shortcut': 'p',
        'description': 'The path to migrations files.',
        'value_required': True
    }]

    needs_config = False

    def fire(self):
        """
        Executes the command.
        """
        creator = MigrationCreator()

        name = self.argument('name')
        table = self.option('table')
        create = bool(self.option('create'))

        if not table and create is not False:
            table = create

        path = self.option('path')
        if path is None:
            path = self._get_migration_path()

        self._write_migration(creator, name, table, create, path)

        self.info('<info>✓ Migration created successfully</info>')

    def _write_migration(self, creator, name, table, create, path):
        """
        Write the migration file to disk.
        """
        file_ = os.path.basename(creator.create(name, path, table, create))

        return file_
