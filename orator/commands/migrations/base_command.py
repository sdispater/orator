# -*- coding: utf-8 -*-

import os
from cleo import Command, InputOption, ListInput
from orator import DatabaseManager


class BaseCommand(Command):

    def __init__(self, resolver=None):
        self._resolver = resolver

        super(BaseCommand, self).__init__()

    def configure(self):
        if not self._resolver:
            self.add_option('config', 'c',
                            InputOption.VALUE_REQUIRED,
                            'The config file path')

    def execute(self, i, o):
        """
        Executes the command.

        :type i: cleo.inputs.input.Input
        :type o: cleo.outputs.output.Output
        """
        if not self._resolver:
            config = self._get_config(i)
            self._resolver = DatabaseManager(config)

    def call(self, name, options=None, o=None):
        """
        Call another command.

        :param name: The command name
        :type name: str

        :param options: The options
        :type options: list or None

        :param o: The output
        :type o: cleo.outputs.output.Output
        """
        if options is None:
            options = []

        command = self.get_application().find(name)

        options = [('command', command.get_name())] + options

        return command.run(ListInput(options), o)

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
