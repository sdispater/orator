# -*- coding: utf-8 -*-

from . import OratorTestCase
from . import mock
from .utils import MockConnection, MockManager

from orator.database_manager import DatabaseManager


class ConnectionTestCase(OratorTestCase):
    def test_connection_method_create_a_new_connection_if_needed(self):
        manager = self._get_manager()
        manager.table("users")

        manager._make_connection.assert_called_once_with("sqlite")

        manager._make_connection.reset_mock()
        manager.table("users")
        self.assertFalse(manager._make_connection.called)

    def test_manager_uses_factory_to_create_connections(self):
        manager = self._get_real_manager()
        original_make = manager._factory.make
        manager._factory.make = mock.MagicMock()
        manager.connection()

        manager._factory.make.assert_called_with(
            {"name": "sqlite", "driver": "sqlite", "database": ":memory:"}, "sqlite"
        )

        manager._factory.make = original_make

    def test_connection_can_select_connections(self):
        manager = self._get_manager()
        self.assertEqual(manager.connection(), manager.connection("sqlite"))
        self.assertNotEqual(manager.connection("sqlite"), manager.connection("sqlite2"))

    def test_dynamic_attribute_gets_connection_attribute(self):
        manager = self._get_manager()
        manager.statement("CREATE TABLE users")

        manager.get_connections()["sqlite"].statement.assert_called_once_with(
            "CREATE TABLE users"
        )

    def test_default_database_with_one_database(self):
        manager = MockManager(
            {"sqlite": {"driver": "sqlite", "database": ":memory:"}}
        ).prepare_mock()

        self.assertEqual("sqlite", manager.get_default_connection())

    def test_reconnect(self):
        manager = self._get_real_manager()

        api_connection = manager.connection().get_connection()
        manager.reconnect()
        self.assertIsNot(manager.connection().get_connection(), api_connection)
        self.assertIsNotNone(manager.connection().get_connection())

    def test_set_default_connection_with_none_should_not_overwrite(self):
        manager = self._get_real_manager()

        manager.set_default_connection(None)

        self.assertEqual("sqlite", manager.get_default_connection())

    def _get_manager(self):
        manager = MockManager(
            {
                "default": "sqlite",
                "sqlite": {"driver": "sqlite", "database": ":memory:"},
                "sqlite2": {"driver": "sqlite", "database": ":memory:"},
            }
        ).prepare_mock()

        return manager

    def _get_real_manager(self):
        manager = DatabaseManager(
            {
                "default": "sqlite",
                "sqlite": {"driver": "sqlite", "database": ":memory:"},
            }
        )

        return manager

    def _get_connection(self):
        return MockConnection().prepare_mock()
