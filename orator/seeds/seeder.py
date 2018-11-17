# -*- coding: utf-8 -*-

from ..orm import Factory


class Seeder(object):

    factory = None

    def __init__(self, resolver=None):
        self._command = None
        self._resolver = resolver

        if self.factory is None:
            self.factory = Factory(resolver=resolver)
        else:
            self.factory.set_connection_resolver(self._resolver)

    def run(self):
        """
        Run the database seeds.
        """
        pass

    def call(self, klass):
        """
        Seed the given connection from the given class.

        :param klass: The Seeder class
        :type klass: class
        """
        self._resolve(klass).run()

        if self._command:
            self._command.line("<info>Seeded:</info> <fg=cyan>%s</>" % klass.__name__)

    def _resolve(self, klass):
        """
        Resolve an instance of the given seeder klass.

        :param klass: The Seeder class
        :type klass: class
        """
        resolver = None

        if self._resolver:
            resolver = self._resolver
        elif self._command:
            resolver = self._command.resolver

        instance = klass()
        instance.set_connection_resolver(resolver)

        if self._command:
            instance.set_command(self._command)

        return instance

    def set_command(self, command):
        """
        Set the console command instance.

        :param command: The command
        :type command: cleo.Command
        """
        self._command = command

        return self

    def set_connection_resolver(self, resolver):
        self._resolver = resolver
        self.factory.set_connection_resolver(resolver)

    @property
    def db(self):
        return self._resolver
