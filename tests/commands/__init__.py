# -*- coding: utf-8 -*-

from flexmock import flexmock_teardown
from cleo import Application, CommandTester
from .. import OratorTestCase


class OratorCommandTestCase(OratorTestCase):
    def tearDown(self):
        flexmock_teardown()

    def run_command(self, command, options=None):
        """
        Run the command.

        :type command: cleo.commands.command.Command
        :type options: list or None
        """
        if options is None:
            options = []

        options = [("command", command.get_name())] + options

        application = Application()
        application.add(command)

        command_tester = CommandTester(command)
        command_tester.execute(options)

        return command_tester
