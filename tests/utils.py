# -*- coding: utf-8 -*-

from . import mock
from orator.connections.connection_interface import ConnectionInterface
from orator.query.processors.processor import QueryProcessor
from orator.database_manager import DatabaseManager
from orator.connectors.connection_factory import ConnectionFactory
from orator.query.builder import QueryBuilder
from orator.orm.model import Model


class MockConnection(ConnectionInterface):

    def set_reconnector(self, reconnector):
        return mock.MagicMock()

    def prepare_mock(self):
        self.table = mock.MagicMock()
        self.select = mock.MagicMock()
        self.insert = mock.MagicMock()
        self.update = mock.MagicMock()
        self.delete = mock.MagicMock()
        self.statement = mock.MagicMock()

        return self


class MockProcessor(QueryProcessor):

    def prepare_mock(self):
        self.process_select = mock.MagicMock()
        self.process_insert_get_id = mock.MagicMock()

        return self


class MockManager(DatabaseManager):

    def prepare_mock(self):
        self._make_connection = mock.MagicMock(
            side_effect=lambda name: MockConnection().prepare_mock()
        )

        return self


class MockFactory(ConnectionFactory):

    def prepare_mock(self):
        self.make = mock.MagicMock(return_value=MockConnection().prepare_mock())

        return self


class MockQueryBuilder(QueryBuilder):

    def prepare_mock(self):
        self.from__ = 'foo_table'

        return self


class MockModel(Model):

    def prepare_mock(self):
        self.get_key_name = mock.MagicMock(return_value='foo')
        self.get_table = mock.MagicMock(return_value='foo_table')
        self.get_qualified_key_name = mock.MagicMock(return_value='foo_table.foo')

        return self
