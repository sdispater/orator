# -*- coding: utf-8 -*-

import os
from flexmock import flexmock
from orator.migrations import MigrationCreator
from orator.commands.migrations import MigrateMakeCommand
from .. import OratorCommandTestCase


class MigrateMakeCommandTestCase(OratorCommandTestCase):

    def test_basic_create_gives_creator_proper_arguments(self):
        creator_mock = flexmock(MigrationCreator)
        creator_mock.should_receive('create').once()\
            .with_args('create_foo', os.path.join(os.getcwd(), 'migrations'), None, False).and_return('foo')

        command = flexmock(MigrateMakeCommand())
        command.should_receive('_get_config').and_return({})

        self.run_command(command, [('name', 'create_foo')])

    def test_basic_create_gives_creator_proper_arguments_when_table_is_set(self):
        creator_mock = flexmock(MigrationCreator)
        creator_mock.should_receive('create').once()\
            .with_args('create_foo', os.path.join(os.getcwd(), 'migrations'), 'users', False).and_return('foo')

        command = flexmock(MigrateMakeCommand())
        command.should_receive('_get_config').and_return({})

        self.run_command(command, [('name', 'create_foo'), ('--table', 'users')])

    def test_basic_create_gives_creator_proper_arguments_when_table_is_set_with_create(self):
        creator_mock = flexmock(MigrationCreator)
        creator_mock.should_receive('create').once()\
            .with_args('create_foo', os.path.join(os.getcwd(), 'migrations'), 'users', True).and_return('foo')

        command = flexmock(MigrateMakeCommand())
        command.should_receive('_get_config').and_return({})

        self.run_command(command, [('name', 'create_foo'), ('--table', 'users'), '--create'])
