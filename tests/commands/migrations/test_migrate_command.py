# -*- coding: utf-8 -*-

import os
from io import BytesIO
from flexmock import flexmock
from cleo import Output
from orator.migrations import Migrator
from orator.commands.migrations import MigrateCommand
from orator import DatabaseManager
from .. import OratorCommandTestCase


class MigrateCommandTestCase(OratorCommandTestCase):

    def test_basic_migrations_call_migrator_with_proper_arguments(self):
        resolver = flexmock(DatabaseManager)
        resolver.should_receive('connection').and_return(None)

        migrator_mock = flexmock(Migrator)
        migrator_mock.should_receive('set_connection').once().with_args(None)
        migrator_mock.should_receive('run').once().with_args(os.path.join(os.getcwd(), 'migrations'), False)
        migrator_mock.should_receive('get_notes').and_return([])
        migrator_mock.should_receive('repository_exists').once().and_return(True)

        command = flexmock(MigrateCommand())
        command.should_receive('_get_config').and_return({})

        self.run_command(command, input_stream=self.get_input_stream('y\n'))

    def test_migration_repository_create_when_necessary(self):
        resolver = flexmock(DatabaseManager)
        resolver.should_receive('connection').and_return(None)

        migrator_mock = flexmock(Migrator)
        migrator_mock.should_receive('set_connection').once().with_args(None)
        migrator_mock.should_receive('run').once().with_args(os.path.join(os.getcwd(), 'migrations'), False)
        migrator_mock.should_receive('get_notes').and_return([])
        migrator_mock.should_receive('repository_exists').once().and_return(False)

        command = flexmock(MigrateCommand())
        command.should_receive('_get_config').and_return({})
        command.should_receive('call').once()\
            .with_args('migrations:install', [('--database', None), ('--config', None)], Output)

        self.run_command(command, input_stream=self.get_input_stream('y\n'))

    def test_migration_can_be_pretended(self):
        resolver = flexmock(DatabaseManager)
        resolver.should_receive('connection').and_return(None)

        migrator_mock = flexmock(Migrator)
        migrator_mock.should_receive('set_connection').once().with_args(None)
        migrator_mock.should_receive('run').once().with_args(os.path.join(os.getcwd(), 'migrations'), True)
        migrator_mock.should_receive('get_notes').and_return([])
        migrator_mock.should_receive('repository_exists').once().and_return(True)

        command = flexmock(MigrateCommand())
        command.should_receive('_get_config').and_return({})

        self.run_command(command, [('--pretend', True)], input_stream=self.get_input_stream('y\n'))

    def test_migration_database_can_be_set(self):
        resolver = flexmock(DatabaseManager)
        resolver.should_receive('connection').and_return(None)

        migrator_mock = flexmock(Migrator)
        migrator_mock.should_receive('set_connection').once().with_args('foo')
        migrator_mock.should_receive('run').once().with_args(os.path.join(os.getcwd(), 'migrations'), False)
        migrator_mock.should_receive('get_notes').and_return([])
        migrator_mock.should_receive('repository_exists').once().and_return(True)

        command = flexmock(MigrateCommand())
        command.should_receive('_get_config').and_return({})

        self.run_command(command, [('--database', 'foo')], input_stream=self.get_input_stream('y\n'))

    def get_input_stream(self, input_):
        stream = BytesIO()
        stream.write(input_.encode())
        stream.seek(0)

        return stream
