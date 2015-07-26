# -*- coding: utf-8 -*-

import importlib
import inflection
import os
from cleo import InputOption
from orator import DatabaseManager
from .base_command import BaseCommand
from ...utils import load_module


class SeedCommand(BaseCommand):

    def __init__(self, resolver=None):
        self._resolver = resolver

        super(SeedCommand, self).__init__()

    def configure(self):
        self.set_name('db:seed')
        self.set_description('Seed the database with records')
        self.add_option('seeder', None, InputOption.VALUE_REQUIRED,
                        'The name of the root seeder.',
                        default='database_seeder')
        self.add_option('database', 'd', InputOption.VALUE_OPTIONAL,
                        'The database connection to use')
        self.add_option('path', 'p', InputOption.VALUE_REQUIRED,
                        'The path of seeds files to be executed. Defaults to <comment>./seeders</comment>')

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
        super(SeedCommand, self).execute(i, o)

        if not self._resolver:
            config = self._get_config(i)
            self._resolver = DatabaseManager(config)

        dialog = self.get_helper('dialog')
        confirm = dialog.ask_confirmation(
            o,
            '<question>Are you sure you want to seed the database?</question> ',
            False
        )
        if not confirm:
            return

        self._resolver.set_default_connection(self._get_database(i))

        self._get_seeder(i).run()

    def _get_seeder(self, i):
        name = self._parse_name(i.get_option('seeder'))
        seeder_file = self._get_path(
            i,
            name
        )

        # Loading parent module
        load_module('seeders', self._get_path(i, '__init__'))

        # Loading module
        mod = load_module('seeders.%s' % name, seeder_file)

        klass = getattr(mod, inflection.camelize(name))

        instance = klass()
        instance.set_command(self)
        instance.set_connection_resolver(self._resolver)

        return instance

    def _parse_name(self, name):
        if name.endswith('.py'):
            name = name.replace('.py', '', -1)

        return name

    def _get_path(self, i, name):
        """
        Get the destination class path.

        :param name: The name
        :type name: str

        :rtype: str
        """
        path = i.get_option('path')
        if path is None:
            path = self._get_seeders_path()

        return os.path.join(path, '%s.py' % name)

    def _get_database(self, i):
        return i.get_option('database')

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

    def get_connection_resolver(self):
        return self._resolver

    def set_connection_resolver(self, resolver):
        self._resolver = resolver
