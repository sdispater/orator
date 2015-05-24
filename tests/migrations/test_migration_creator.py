# -*- coding: utf-8 -*-

import tempfile
import os
from flexmock import flexmock, flexmock_teardown
from orator.migrations import MigrationCreator
from orator.migrations.stubs import CREATE_STUB, UPDATE_STUB, BLANK_STUB
from .. import OratorTestCase


class MigrationCreatorTestCase(OratorTestCase):

    def tearDown(self):
        flexmock_teardown()

    def test_basic_create_method_stores_migration_file(self):
        expected = os.path.join(tempfile.gettempdir(), 'foo_create_bar.py')
        if os.path.exists(expected):
            os.remove(expected)

        creator = self.get_creator()
        creator.should_receive('_get_date_prefix').and_return('foo')
        creator.create('create_bar', tempfile.gettempdir())

        self.assertTrue(os.path.exists(expected))
        with open(expected) as fh:
            content = fh.read()
            self.assertEqual(content, BLANK_STUB.replace('DummyClass', 'CreateBar'))

        os.remove(expected)

    def test_table_update_migration_stores_migration_file(self):
        expected = os.path.join(tempfile.gettempdir(), 'foo_create_bar.py')
        if os.path.exists(expected):
            os.remove(expected)

        creator = self.get_creator()
        creator.should_receive('_get_date_prefix').and_return('foo')
        creator.create('create_bar', tempfile.gettempdir(), 'baz')

        self.assertTrue(os.path.exists(expected))
        with open(expected) as fh:
            content = fh.read()
            self.assertEqual(content, UPDATE_STUB.replace('DummyClass', 'CreateBar').replace('dummy_table', 'baz'))

        os.remove(expected)

    def test_table_create_migration_stores_migration_file(self):
        expected = os.path.join(tempfile.gettempdir(), 'foo_create_bar.py')
        if os.path.exists(expected):
            os.remove(expected)

        creator = self.get_creator()
        creator.should_receive('_get_date_prefix').and_return('foo')
        creator.create('create_bar', tempfile.gettempdir(), 'baz', True)

        self.assertTrue(os.path.exists(expected))
        with open(expected) as fh:
            content = fh.read()
            self.assertEqual(content, CREATE_STUB.replace('DummyClass', 'CreateBar').replace('dummy_table', 'baz'))

        os.remove(expected)

    def get_creator(self):
        return flexmock(MigrationCreator())
