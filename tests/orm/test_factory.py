# -*- coding: utf-8 -*-

from orator.orm import Factory, Model, belongs_to, has_many
from orator.connections import SQLiteConnection
from orator.connectors import SQLiteConnector

from .. import OratorTestCase, mock


class FactoryTestCase(OratorTestCase):
    @classmethod
    def setUpClass(cls):
        Model.set_connection_resolver(DatabaseConnectionResolver())

    @classmethod
    def tearDownClass(cls):
        Model.unset_connection_resolver()

    def connection(self):
        return Model.get_connection_resolver().connection()

    def schema(self):
        return self.connection().get_schema_builder()

    def setUp(self):
        with self.schema().create("users") as table:
            table.increments("id")
            table.string("name").unique()
            table.string("email").unique()
            table.boolean("admin").default(True)
            table.timestamps()

        with self.schema().create("posts") as table:
            table.increments("id")
            table.integer("user_id")
            table.string("title").unique()
            table.text("content").unique()
            table.timestamps()

            table.foreign("user_id").references("id").on("users")

        self.factory = Factory()

        @self.factory.define(User)
        def users_factory(faker):
            return {"name": faker.name(), "email": faker.email(), "admin": False}

        @self.factory.define(User, "admin")
        def users_factory(faker):
            attributes = self.factory.raw(User)

            attributes.update({"admin": True})

            return attributes

        @self.factory.define(Post)
        def posts_factory(faker):
            return {"title": faker.sentence(), "content": faker.text()}

    def tearDown(self):
        self.schema().drop("posts")
        self.schema().drop("users")

    def test_factory_make(self):
        user = self.factory.make(User)

        self.assertIsInstance(user, User)
        self.assertIsNotNone(user.name)
        self.assertIsNotNone(user.email)
        self.assertIsNone(User.where("name", user.name).first())

    def test_factory_create(self):
        user = self.factory.create(User)

        self.assertIsInstance(user, User)
        self.assertIsNotNone(user.name)
        self.assertIsNotNone(user.email)
        self.assertIsNotNone(User.where("name", user.name).first())

    def test_factory_create_with_attributes(self):
        user = self.factory.create(User, name="foo", email="foo@bar.com")

        self.assertIsInstance(user, User)
        self.assertEqual("foo", user.name)
        self.assertEqual("foo@bar.com", user.email)
        self.assertIsNotNone(User.where("name", user.name).first())

    def test_factory_create_with_relations(self):
        users = self.factory.build(User, 3)
        users = users.create().each(lambda u: u.posts().save(self.factory.make(Post)))

        self.assertEqual(3, len(users))
        self.assertIsInstance(users[0], User)
        self.assertEqual(3, User.count())
        self.assertEqual(3, Post.count())

    def test_factory_call(self):
        user = self.factory(User).create()
        self.assertFalse(user.admin)

        users = self.factory(User, 3).create()

        self.assertEqual(3, len(users))
        self.assertFalse(users[0].admin)

        admin = self.factory(User, "admin").create()
        self.assertTrue(admin.admin)

        admins = self.factory(User, "admin", 3).create()
        self.assertEqual(3, len(admins))
        self.assertTrue(admins[0].admin)


class User(Model):

    __guarded__ = ["id"]

    @has_many("user_id")
    def posts(self):
        return Post


class Post(Model):

    __guarded__ = []

    @belongs_to("user_id")
    def user(self):
        return User


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
