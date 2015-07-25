# -*- coding: utf-8 -*-

import os
import errno
import inflection
from cleo import InputArgument, InputOption
from ...seeds.stubs import DEFAULT_STUB
from .base_command import BaseCommand


class SeedersMakeCommand(BaseCommand):

    def configure(self):
        self.set_name('seeders:make')
        self.set_description('Create a new seeder file')
        self.add_argument('name', InputArgument.REQUIRED, 'The name of the seed.')
        self.add_option('path', 'p', InputOption.VALUE_OPTIONAL,
                        'The path to seeders files.')

    def execute(self, i, o):
        """
        Executes the command.

        :type i: cleo.inputs.input.Input
        :type o: cleo.outputs.output.Output
        """
        super(SeedersMakeCommand, self).execute(i, o)

        # Making root seeder
        self._make(i, o, 'database_seeder', True)

        self._make(i, o, self._get_name_input(i))

    def _make(self, i, o, name, root=False):
        name = self._parse_name(name)

        path = self._get_path(i, name)
        if os.path.exists(path):
            if not root:
                o.writeln('<error>%s already exists</error>' % name)

            return False

        self._make_directory(os.path.dirname(path))

        with open(path, 'w') as fh:
            fh.write(self._build_class(name))

        if root:
            with open(os.path.join(os.path.dirname(path), '__init__.py'), 'w'):
                pass

        o.writeln('<info><fg=cyan>%s</> created successfully.</info>' % name)

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

    def _make_directory(self, path):
        try:
            os.makedirs(path)
        except OSError as exc:
            if exc.errno == errno.EEXIST and os.path.isdir(path):
                pass
            else:
                raise

    def _build_class(self, name):
        stub = self._get_stub()
        klass = self._get_class_name(name)

        stub = stub.replace('DummyClass', klass)

        return stub

    def _get_stub(self):
        return DEFAULT_STUB

    def _get_class_name(self, name):
        return inflection.camelize(name)

    def _get_name_input(self, i):
        return i.get_argument('name')
