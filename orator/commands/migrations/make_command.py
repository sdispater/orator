# -*- coding: utf-8 -*-

import os
from cleo import InputOption, InputArgument, ListInput
from orator.migrations import MigrationCreator, DatabaseMigrationRepository
from .base_command import BaseCommand
from ...utils import decode


class MigrateMakeCommand(BaseCommand):

    def configure(self):
        super(MigrateMakeCommand, self).configure()

        self.set_name('migrations:make')
        self.set_description('Create a new migration file')
        self.add_argument('name', InputArgument.REQUIRED, 'The name of the migration.')
        self.add_option('create', 'C', InputOption.VALUE_NONE,
                        'The table to be created.')
        self.add_option('table', 't', InputOption.VALUE_OPTIONAL,
                        'The table to migrate.')
        self.add_option('path', 'p', InputOption.VALUE_OPTIONAL,
                        'The path of migrations files.')

    def execute(self, i, o):
        """
        Executes the command.

        :type i: cleo.inputs.input.Input
        :type o: cleo.outputs.output.Output
        """
        super(MigrateMakeCommand, self).execute(i, o)

        creator = MigrationCreator()

        name = i.get_argument('name')
        table = i.get_option('table')
        create = bool(i.get_option('create'))

        if not table and create is not False:
            table = create

        path = i.get_option('path')
        if path is None:
            path = self._get_migration_path()

        file_ = self._write_migration(creator, name, table, create, path)

        o.writeln(decode('<info>✓ Migration created successfully</info>'))

    def _write_migration(self, creator, name, table, create, path):
        """
        Write the migration file to disk.
        """
        file_ = os.path.basename(creator.create(name, path, table, create))

        return file_
