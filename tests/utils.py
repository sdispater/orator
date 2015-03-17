# -*- coding: utf-8 -*-

from . import mock
from eloquent.connections.connection_interface import ConnectionInterface
from eloquent.query.processors.processor import QueryProcessor
from eloquent.database_manager import DatabaseManager
from eloquent.connectors.connection_factory import ConnectionFactory


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
