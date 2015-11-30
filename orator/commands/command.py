# -*- coding: utf-8 -*-

import os
from cleo import Command as BaseCommand, InputOption, ListInput
from orator import DatabaseManager
import yaml


class Command(BaseCommand):

    needs_config = True

    def __init__(self, resolver=None):
        self.resolver = resolver
        self.input = None
        self.output = None

        super(Command, self).__init__()

    def initialize(self, i, o):
        """
        Initialize command.

        :type i: cleo.inputs.input.Input
        :type o: cleo.outputs.output.Output
        """
        self.input = i
        self.output = o

    def configure(self):
        super(Command, self).configure()

        if self.needs_config and not self.resolver:
            # Checking if a default config file is present
            if not self._check_config():
                self.add_option('config', 'c',
                                InputOption.VALUE_REQUIRED,
                                'The config file path')

    def execute(self, i, o):
        """
        Executes the command.

        :type i: cleo.inputs.input.Input
        :type o: cleo.outputs.output.Output
        """
        if self.needs_config and not self.resolver:
            self._handle_config(self.option('config'))

        return self.fire()

    def fire(self):
        """
        Executes the command.
        """
        raise NotImplementedError()

    def call(self, name, options=None):
        """
        Call another command.

        :param name: The command name
        :type name: str

        :param options: The options
        :type options: list or None
        """
        if options is None:
            options = []

        command = self.get_application().find(name)
        if self.resolver:
            command.resolver = self.resolver

        options = [('command', command.get_name())] + options

        return command.run(ListInput(options), self.output)

    def _get_migration_path(self):
        return os.path.join(os.getcwd(), 'migrations')

    def _check_config(self):
        """
        Check presence of default config files.

        :rtype: bool
        """
        current_path = os.path.relpath(os.getcwd())

        accepted_files = ['orator.yml', 'orator.py']
        for accepted_file in accepted_files:
            config_file = os.path.join(current_path, accepted_file)
            if os.path.exists(config_file):
                if self._handle_config(config_file):
                    return True

        return False

    def _handle_config(self, config_file):
        """
        Check and handle a config file.

        :param config_file: The path to the config file
        :type config_file: str

        :rtype: bool
        """
        config = self._get_config(config_file)

        self.resolver = DatabaseManager(config.get('databases', config.get('DATABASES', {})))

        return True

    def _get_config(self, path=None):
        """
        Get the config.

        :rtype: dict
        """
        if not path and not self.option('config'):
            raise Exception('The --config|-c option is missing.')

        if not path:
            path = self.option('config')

        filename, ext = os.path.splitext(path)
        if ext in ['.yml', '.yaml']:
            with open(path) as fd:
                config = yaml.load(fd)
        elif ext in ['.py']:
            config = {}

            with open(path) as fh:
                exec(fh.read(), {}, config)
        else:
            raise RuntimeError('Config file [%s] is not supported.' % path)

        return config

    def line(self, text):
        """
        Write a string as information output.

        :param text: The line to write
        :type text: str
        """
        self.output.writeln(text)

    def info(self, text):
        """
        Write a string as information output.

        :param text: The line to write
        :type text: str
        """
        self.line('<info>%s</info>' % text)

    def comment(self, text):
        """
        Write a string as comment output.

        :param text: The line to write
        :type text: str
        """
        self.line('<comment>%s</comment>' % text)

    def question(self, text):
        """
        Write a string as question output.

        :param text: The line to write
        :type text: str
        """
        self.line('<question>%s</question>' % text)

    def error(self, text):
        """
        Write a string as error output.

        :param text: The line to write
        :type text: str
        """
        self.line('<error>%s</error>' % text)

    def argument(self, key=None):
        if key is None:
            return self.input.get_arguments()

        return self.input.get_argument(key)

    def option(self, key=None):
        if key is None:
            return self.input.get_options()

        return self.input.get_option(key)
