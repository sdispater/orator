# -*- coding: utf-8 -*-

from . import mock
from eloquent.connections.connection_interface import ConnectionInterface
from eloquent.query.processors.processor import QueryProcessor


class MockConnection(ConnectionInterface):

    def prepare_mock(self):
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
