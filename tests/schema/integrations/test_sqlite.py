# -*- coding: utf-8 -*-

from ... import OratorTestCase
from . import IntegrationTestCase, User, Post
from orator import Model
from orator.connections import SQLiteConnection
from orator.connectors.sqlite_connector import SQLiteConnector


class SchemaBuilderSQLiteIntegrationTestCase(IntegrationTestCase, OratorTestCase):
    @classmethod
    def get_connection_resolver(cls):
        return DatabaseIntegrationConnectionResolver()

    def test_foreign_keys_creation(self):
        pass

    def test_rename_columns_with_foreign_keys(self):
        super(
            SchemaBuilderSQLiteIntegrationTestCase, self
        ).test_rename_columns_with_foreign_keys()

        old_foreign_keys = (
            self.connection().get_schema_manager().list_table_foreign_keys("friends")
        )

        with self.schema().table("friends") as table:
            table.rename_column("user_id", "my_user_id")

        foreign_keys = (
            self.connection().get_schema_manager().list_table_foreign_keys("friends")
        )

        self.assertEqual(len(old_foreign_keys), len(foreign_keys))


class SchemaBuilderSQLiteIntegrationCascadingTestCase(OratorTestCase):
    @classmethod
    def setUpClass(cls):
        Model.set_connection_resolver(
            DatabaseIntegrationConnectionWithoutForeignKeysResolver()
        )

    @classmethod
    def tearDownClass(cls):
        Model.unset_connection_resolver()

    def setUp(self):
        with self.schema().create("users") as table:
            table.increments("id")
            table.string("email").unique()
            table.timestamps()

        with self.schema().create("friends") as table:
            table.integer("user_id")
            table.integer("friend_id")

            table.foreign("user_id").references("id").on("users").on_delete("cascade")
            table.foreign("friend_id").references("id").on("users").on_delete("cascade")

        with self.schema().create("posts") as table:
            table.increments("id")
            table.integer("user_id")
            table.string("name").unique()
            table.timestamps()

            table.foreign("user_id").references("id").on("users")

        with self.schema().create("photos") as table:
            table.increments("id")
            table.morphs("imageable")
            table.string("name")
            table.timestamps()

        for i in range(10):
            user = User.create(email="user%d@foo.com" % (i + 1))

            for j in range(10):
                post = Post(name="User %d Post %d" % (user.id, j + 1))
                user.posts().save(post)

    def tearDown(self):
        self.schema().drop("photos")
        self.schema().drop("posts")
        self.schema().drop("friends")
        self.schema().drop("users")

    def test_cascading(self):
        user = User.create(email="john@doe.com")
        friend = User.create(email="jane@doe.com")
        another_friend = User.create(email="another@doe.com")
        user.friends().attach(friend)
        user.friends().attach(another_friend)

        user.delete()

        self.assertEqual(
            2, user.get_connection_resolver().connection().table("friends").count()
        )

    def connection(self):
        return Model.get_connection_resolver().connection()

    def schema(self):
        return self.connection().get_schema_builder()


class DatabaseIntegrationConnectionResolver(object):

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


class DatabaseIntegrationConnectionWithoutForeignKeysResolver(
    DatabaseIntegrationConnectionResolver
):

    _connection = None

    def connection(self, name=None):
        if self._connection:
            return self._connection

        self._connection = SQLiteConnection(
            SQLiteConnector().connect({"database": ":memory:", "foreign_keys": False})
        )

        return self._connection
