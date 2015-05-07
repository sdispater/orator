# -*- coding: utf-8 -*-

import os
from cleo import Command, InputOption
from eloquent import DatabaseManager


class BaseCommand(Command):

    def __init__(self):
        super(BaseCommand, self).__init__()

        self._resolver = {}

    def configure(self):
        self.add_option('config', 'c', InputOption.VALUE_REQUIRED, 'The config file path')

    def execute(self, i, o):
        """
        Executes the command.

        :type i: cleo.inputs.input.Input
        :type o: cleo.outputs.output.Output
        """
        config = self._get_config(i)
        self._resolver = DatabaseManager(config)

    def _get_migration_path(self):
        return os.path.join(os.getcwd(), 'migrations')

    def _get_config(self, i):
        """
        Get the config.

        :type i: cleo.inputs.input.Input

        :rtype: dict
        """
        variables = {}
        if not i.get_option('config'):
            raise Exception('The --config|-c option is missing.')

        with open(i.get_option('config')) as fh:
            exec(fh.read(), {}, variables)

        return variables['DATABASES']
