# -*- coding:utf-8 -*-
import os
import tempfile

from flexmock import flexmock

from orator.commands.command import Command

from . import OratorCommandTestCase


class FooCommand(Command):
    """
    Test Command
    """

    name = "foo"

    def handle(self):
        pass


class CommandTestCase(OratorCommandTestCase):
    def test_get_py_config_and_require___file__(self):
        filename = tempfile.mktemp(".py")
        with open(filename, "w") as f:
            f.write("foo = __file__")

        command = flexmock(FooCommand())
        command.should_call("_get_config").and_return({"foo": filename})

        self.run_command(command, [("-c", filename)])

        if os.path.exists(filename):
            os.remove(filename)
