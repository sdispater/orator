# -*- coding: utf-8 -*-

import os
from io import BytesIO
from flexmock import flexmock
from orator.migrations import Migrator
from orator.commands.migrations import ResetCommand
from orator import DatabaseManager
from .. import OratorCommandTestCase


class ResetCommandTestCase(OratorCommandTestCase):

    def test_basic_migrations_call_migrator_with_proper_arguments(self):
        resolver = flexmock(DatabaseManager)
        resolver.should_receive('connection').and_return(None)

        migrator_mock = flexmock(Migrator)
        migrator_mock.should_receive('set_connection').once().with_args(None)
        migrator_mock.should_receive('rollback').twice()\
            .with_args(os.path.join(os.getcwd(), 'migrations'), False)\
            .and_return(1, 0).one_by_one()
        migrator_mock.should_receive('get_notes').and_return([])

        command = flexmock(ResetCommand())
        command.should_receive('_get_config').and_return({})

        self.run_command(command, input_stream=self.get_input_stream('y\n'))

    def test_migration_can_be_pretended(self):
        resolver = flexmock(DatabaseManager)
        resolver.should_receive('connection').and_return(None)

        migrator_mock = flexmock(Migrator)
        migrator_mock.should_receive('set_connection').once().with_args(None)
        migrator_mock.should_receive('rollback').twice()\
            .with_args(os.path.join(os.getcwd(), 'migrations'), True)\
            .and_return(1, 0).one_by_one()
        migrator_mock.should_receive('get_notes').and_return([])

        command = flexmock(ResetCommand())
        command.should_receive('_get_config').and_return({})

        self.run_command(command, [('--pretend', True)], input_stream=self.get_input_stream('y\n'))

    def test_migration_database_can_be_set(self):
        resolver = flexmock(DatabaseManager)
        resolver.should_receive('connection').and_return(None)

        migrator_mock = flexmock(Migrator)
        migrator_mock.should_receive('set_connection').once().with_args('foo')
        migrator_mock.should_receive('rollback').twice()\
            .with_args(os.path.join(os.getcwd(), 'migrations'), False)\
            .and_return(1, 0).one_by_one()
        migrator_mock.should_receive('get_notes').and_return([])

        command = flexmock(ResetCommand())
        command.should_receive('_get_config').and_return({})

        self.run_command(command, [('--database', 'foo')], input_stream=self.get_input_stream('y\n'))

    def get_input_stream(self, input_):
        stream = BytesIO()
        stream.write(input_.encode())
        stream.seek(0)

        return stream
