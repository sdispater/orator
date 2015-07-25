# -*- coding: utf-8 -*-

import os
from cleo import Command


class BaseCommand(Command):

    def __init__(self, name=None):
        super(BaseCommand, self).__init__(name)

        self._input = None
        self._output = None

    def _get_seeders_path(self):
        return os.path.join(os.getcwd(), 'seeders')

    def execute(self, i, o):
        self._input = i
        self._output = o

    def get_output(self):
        return self._output
