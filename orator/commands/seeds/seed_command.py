# -*- coding: utf-8 -*-

import importlib
import inflection
import os
from cleo import InputOption
from orator import DatabaseManager
from .base_command import BaseCommand
from ...utils import load_module


class SeedCommand(BaseCommand):
    """
    Seed the database with records.

    db:seed
        {--d|database= : The database connection to use.}
        {--p|path= : The path to seeders files.
                     Defaults to <comment>./seeds</comment>.}
        {--seeder=database_seeder : The name of the root seeder.}
        {--f|force : Force the operation to run.}
    """

    def handle(self):
        """
        Executes the command.
        """
        if not self.confirm_to_proceed(
            "<question>Are you sure you want to seed the database?:</question> "
        ):
            return

        self.resolver.set_default_connection(self.option("database"))

        self._get_seeder().run()

        self.info("Database seeded!")

    def _get_seeder(self):
        name = self._parse_name(self.option("seeder"))
        seeder_file = self._get_path(name)

        # Loading parent module
        load_module("seeds", self._get_path("__init__"))

        # Loading module
        mod = load_module("seeds.%s" % name, seeder_file)

        klass = getattr(mod, inflection.camelize(name))

        instance = klass()
        instance.set_command(self)
        instance.set_connection_resolver(self.resolver)

        return instance

    def _parse_name(self, name):
        if name.endswith(".py"):
            name = name.replace(".py", "", -1)

        return name

    def _get_path(self, name):
        """
        Get the destination class path.

        :param name: The name
        :type name: str

        :rtype: str
        """
        path = self.option("path")
        if path is None:
            path = self._get_seeders_path()

        return os.path.join(path, "%s.py" % name)
