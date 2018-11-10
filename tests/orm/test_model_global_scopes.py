# -*- coding: utf-8 -*-

from .. import OratorTestCase
from orator.orm.scopes import Scope
from orator import Model
from orator.connections import SQLiteConnection
from orator.connectors import SQLiteConnector


class ModelGlobalScopesTestCase(OratorTestCase):
    @classmethod
    def setUpClass(cls):
        Model.set_connection_resolver(DatabaseConnectionResolver())

    @classmethod
    def tearDownClass(cls):
        Model.unset_connection_resolver()

    def test_global_scope_is_applied(self):
        model = GlobalScopesModel()
        query = model.new_query()

        self.assertEqual('SELECT * FROM "table" WHERE "active" = ?', query.to_sql())

        self.assertEqual([1], query.get_bindings())

    def test_global_scope_can_be_removed(self):
        model = GlobalScopesModel()
        query = model.new_query().without_global_scope(ActiveScope)

        self.assertEqual('SELECT * FROM "table"', query.to_sql())

        self.assertEqual([], query.get_bindings())

    def test_callable_global_scope_is_applied(self):
        model = CallableGlobalScopesModel()
        query = model.new_query()

        self.assertEqual(
            'SELECT * FROM "table" WHERE "active" = ? ORDER BY "name" ASC',
            query.to_sql(),
        )

        self.assertEqual([1], query.get_bindings())

    def test_callable_global_scope_can_be_removed(self):
        model = CallableGlobalScopesModel()
        query = model.new_query().without_global_scope("active_scope")

        self.assertEqual('SELECT * FROM "table" ORDER BY "name" ASC', query.to_sql())

        self.assertEqual([], query.get_bindings())

    def test_global_scope_can_be_removed_after_query_is_executed(self):
        model = CallableGlobalScopesModel()
        query = model.new_query()

        self.assertEqual(
            'SELECT * FROM "table" WHERE "active" = ? ORDER BY "name" ASC',
            query.to_sql(),
        )
        self.assertEqual([1], query.get_bindings())

        query.without_global_scope("active_scope")

        self.assertEqual('SELECT * FROM "table" ORDER BY "name" ASC', query.to_sql())
        self.assertEqual([], query.get_bindings())

    def test_all_global_scopes_can_be_removed(self):
        model = CallableGlobalScopesModel()
        query = model.new_query().without_global_scopes()

        self.assertEqual('SELECT * FROM "table"', query.to_sql())
        self.assertEqual([], query.get_bindings())

        query = CallableGlobalScopesModel.without_global_scopes()
        self.assertEqual('SELECT * FROM "table"', query.to_sql())
        self.assertEqual([], query.get_bindings())

    def test_global_scopes_with_or_where_conditions_are_nested(self):
        model = CallableGlobalScopesModelWithOr()

        query = model.new_query().where("col1", "val1").or_where("col2", "val2")
        self.assertEqual(
            'SELECT "email", "password" FROM "table" '
            'WHERE ("col1" = ? OR "col2" = ?) AND ("email" = ? OR "email" = ?) '
            'AND ("active" = ?) ORDER BY "name" ASC',
            query.to_sql(),
        )
        self.assertEqual(
            ["val1", "val2", "john@doe.com", "someone@else.com", True],
            query.get_bindings(),
        )


class CallableGlobalScopesModel(Model):

    __table__ = "table"

    @classmethod
    def _boot(cls):
        cls.add_global_scope("active_scope", lambda query: query.where("active", 1))

        cls.add_global_scope(lambda query: query.order_by("name"))

        super(CallableGlobalScopesModel, cls)._boot()


class CallableGlobalScopesModelWithOr(CallableGlobalScopesModel):

    __table__ = "table"

    @classmethod
    def _boot(cls):
        cls.add_global_scope(
            "or_scope",
            lambda q: q.where("email", "john@doe.com").or_where(
                "email", "someone@else.com"
            ),
        )

        cls.add_global_scope(lambda query: query.select("email", "password"))

        super(CallableGlobalScopesModelWithOr, cls)._boot()


class GlobalScopesModel(Model):

    __table__ = "table"

    @classmethod
    def _boot(cls):
        cls.add_global_scope(ActiveScope())

        super(GlobalScopesModel, cls)._boot()


class ActiveScope(Scope):
    def apply(self, builder, model):
        return builder.where("active", 1)


class DatabaseConnectionResolver(object):

    _connection = None

    def connection(self, name=None):
        if self._connection:
            return self._connection

        self._connection = SQLiteConnection(
            SQLiteConnector().connect({"database": ":memory:"})
        )

        return self._connection

    def get_default_connection(self):
        return "default"

    def set_default_connection(self, name):
        pass
