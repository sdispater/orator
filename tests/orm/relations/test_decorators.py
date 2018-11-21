# -*- coding: utf-8 -*-

from ... import OratorTestCase
from orator import Model as BaseModel
from orator.orm import (
    morph_to,
    has_one,
    has_many,
    belongs_to_many,
    morph_many,
    belongs_to,
)
from orator.orm.model import ModelRegister
from orator.connections import SQLiteConnection
from orator.connectors.sqlite_connector import SQLiteConnector


class DecoratorsTestCase(OratorTestCase):
    @classmethod
    def setUpClass(cls):
        Model.set_connection_resolver(DatabaseIntegrationConnectionResolver())

    @classmethod
    def tearDownClass(cls):
        Model.unset_connection_resolver()

    def setUp(self):
        with self.schema().create("test_users") as table:
            table.increments("id")
            table.string("email").unique()
            table.timestamps()

        with self.schema().create("test_friends") as table:
            table.increments("id")
            table.integer("user_id")
            table.integer("friend_id")

        with self.schema().create("test_posts") as table:
            table.increments("id")
            table.integer("user_id")
            table.string("name")
            table.timestamps()
            table.soft_deletes()

        with self.schema().create("test_photos") as table:
            table.increments("id")
            table.morphs("imageable")
            table.string("name")
            table.timestamps()

    def tearDown(self):
        self.schema().drop("test_users")
        self.schema().drop("test_friends")
        self.schema().drop("test_posts")
        self.schema().drop("test_photos")

    def test_extra_queries_are_properly_set_on_relations(self):
        self.create()

        # With eager loading
        user = OratorTestUser.with_("friends", "posts", "post", "photos").find(1)
        post = OratorTestPost.with_("user", "photos").find(1)
        self.assertEqual(1, len(user.friends))
        self.assertEqual(2, len(user.posts))
        self.assertIsInstance(user.post, OratorTestPost)
        self.assertEqual(3, len(user.photos))
        self.assertIsInstance(post.user, OratorTestUser)
        self.assertEqual(2, len(post.photos))
        self.assertEqual(
            'SELECT * FROM "test_users" INNER JOIN "test_friends" ON "test_users"."id" = "test_friends"."friend_id" '
            'WHERE "test_friends"."user_id" = ? ORDER BY "friend_id" ASC',
            user.friends().to_sql(),
        )
        self.assertEqual(
            'SELECT * FROM "test_posts" WHERE "deleted_at" IS NULL AND "test_posts"."user_id" = ?',
            user.posts().to_sql(),
        )
        self.assertEqual(
            'SELECT * FROM "test_posts" WHERE "test_posts"."user_id" = ? ORDER BY "name" DESC',
            user.post().to_sql(),
        )
        self.assertEqual(
            'SELECT * FROM "test_photos" WHERE "name" IS NOT NULL AND "test_photos"."imageable_id" = ? AND "test_photos"."imageable_type" = ?',
            user.photos().to_sql(),
        )
        self.assertEqual(
            'SELECT * FROM "test_users" WHERE "test_users"."id" = ? ORDER BY "id" ASC',
            post.user().to_sql(),
        )
        self.assertEqual(
            'SELECT * FROM "test_photos" WHERE "test_photos"."imageable_id" = ? AND "test_photos"."imageable_type" = ?',
            post.photos().to_sql(),
        )

        # Without eager loading
        user = OratorTestUser.find(1)
        post = OratorTestPost.find(1)
        self.assertEqual(1, len(user.friends))
        self.assertEqual(2, len(user.posts))
        self.assertIsInstance(user.post, OratorTestPost)
        self.assertEqual(3, len(user.photos))
        self.assertIsInstance(post.user, OratorTestUser)
        self.assertEqual(2, len(post.photos))
        self.assertEqual(
            'SELECT * FROM "test_users" INNER JOIN "test_friends" ON "test_users"."id" = "test_friends"."friend_id" '
            'WHERE "test_friends"."user_id" = ? ORDER BY "friend_id" ASC',
            user.friends().to_sql(),
        )
        self.assertEqual(
            'SELECT * FROM "test_posts" WHERE "deleted_at" IS NULL AND "test_posts"."user_id" = ?',
            user.posts().to_sql(),
        )
        self.assertEqual(
            'SELECT * FROM "test_posts" WHERE "test_posts"."user_id" = ? ORDER BY "name" DESC',
            user.post().to_sql(),
        )
        self.assertEqual(
            'SELECT * FROM "test_photos" WHERE "name" IS NOT NULL AND "test_photos"."imageable_id" = ? AND "test_photos"."imageable_type" = ?',
            user.photos().to_sql(),
        )
        self.assertEqual(
            'SELECT * FROM "test_users" WHERE "test_users"."id" = ? ORDER BY "id" ASC',
            post.user().to_sql(),
        )
        self.assertEqual(
            'SELECT * FROM "test_photos" WHERE "test_photos"."imageable_id" = ? AND "test_photos"."imageable_type" = ?',
            post.photos().to_sql(),
        )

        self.assertEqual(
            'SELECT DISTINCT * FROM "test_posts" WHERE "deleted_at" IS NULL AND "test_posts"."user_id" = ? ORDER BY "user_id" ASC',
            user.posts().order_by("user_id").distinct().to_sql(),
        )

    def create(self):
        user = OratorTestUser.create(id=1, email="john@doe.com")
        friend = OratorTestUser.create(id=2, email="jane@doe.com")
        user.friends().attach(friend)

        post1 = user.posts().create(name="First Post")
        post2 = user.posts().create(name="Second Post")

        user.photos().create(name="Avatar 1")
        user.photos().create(name="Avatar 2")
        user.photos().create(name="Avatar 3")

        post1.photos().create(name="Hero 1")
        post1.photos().create(name="Hero 2")

    def connection(self):
        return Model.get_connection_resolver().connection()

    def schema(self):
        return self.connection().get_schema_builder()


class Model(BaseModel):

    _register = ModelRegister()


class OratorTestUser(Model):

    __table__ = "test_users"
    __guarded__ = []

    @belongs_to_many("test_friends", "user_id", "friend_id", with_pivot=["id"])
    def friends(self):
        return OratorTestUser.order_by("friend_id")

    @has_many("user_id")
    def posts(self):
        return OratorTestPost.where_null("deleted_at")

    @has_one("user_id")
    def post(self):
        return OratorTestPost.order_by("name", "desc")

    @morph_many("imageable")
    def photos(self):
        return OratorTestPhoto.where_not_null("name")


class OratorTestPost(Model):

    __table__ = "test_posts"
    __guarded__ = []

    @belongs_to("user_id")
    def user(self):
        return OratorTestUser.order_by("id")

    @morph_many("imageable")
    def photos(self):
        return "test_photos"


class OratorTestPhoto(Model):

    __table__ = "test_photos"
    __guarded__ = []

    @morph_to
    def imageable(self):
        return


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
