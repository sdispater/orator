# -*- coding: utf-8 -*-

from cleo import InputOption
from orator.migrations import DatabaseMigrationRepository
from .base_command import BaseCommand
from ...utils import decode


class InstallCommand(BaseCommand):

    def configure(self):
        super(InstallCommand, self).configure()

        self.set_name('migrations:install')
        self.set_description('Create the migration repository')
        self.add_option('database', 'd', InputOption.VALUE_OPTIONAL,
                        'The database connection to use')

    def execute(self, i, o):
        """
        Executes the command.

        :type i: cleo.inputs.input.Input
        :type o: cleo.outputs.output.Output
        """
        super(InstallCommand, self).execute(i, o)

        database = i.get_option('database')
        repository = DatabaseMigrationRepository(self._resolver, 'migrations')

        repository.set_source(database)
        repository.create_repository()

        o.writeln(decode('<info>✓ Migration table created successfully</info>'))
