# -*- coding: utf-8 -*-

from orator import Model
from orator.orm import (
    has_one,
    has_many,
    belongs_to,
    belongs_to_many,
    morph_to,
    morph_many,
)
from orator import QueryExpression
from orator.dbal.exceptions import ColumnDoesNotExist


class IntegrationTestCase(object):
    @classmethod
    def setUpClass(cls):
        Model.set_connection_resolver(cls.get_connection_resolver())

    @classmethod
    def get_connection_resolver(cls):
        raise NotImplementedError()

    @classmethod
    def tearDownClass(cls):
        Model.unset_connection_resolver()

    def setUp(self):
        with self.connection().transaction():
            self.schema().drop_if_exists("photos")
            self.schema().drop_if_exists("posts")
            self.schema().drop_if_exists("friends")
            self.schema().drop_if_exists("users")

            with self.schema().create("users") as table:
                table.increments("id")
                table.string("email").unique()
                table.integer("votes").default(0)
                table.timestamps(use_current=True)

            with self.schema().create("friends") as table:
                table.integer("user_id", unsigned=True)
                table.integer("friend_id", unsigned=True)

                table.foreign("user_id").references("id").on("users").on_delete(
                    "cascade"
                )
                table.foreign("friend_id").references("id").on("users").on_delete(
                    "cascade"
                )

            with self.schema().create("posts") as table:
                table.increments("id")
                table.integer("user_id", unsigned=True)
                table.string("name").unique()
                table.enum("status", ["draft", "published"]).default("draft").nullable()
                table.string("default").default(0)
                table.string("tag").nullable().default("tag")
                table.timestamps(use_current=True)

                table.foreign("user_id", "users_foreign_key").references("id").on(
                    "users"
                )

            with self.schema().create("photos") as table:
                table.increments("id")
                table.morphs("imageable")
                table.string("name")
                table.timestamps(use_current=True)

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

    def test_foreign_keys_creation(self):
        posts_foreign_keys = (
            self.connection().get_schema_manager().list_table_foreign_keys("posts")
        )
        friends_foreign_keys = (
            self.connection().get_schema_manager().list_table_foreign_keys("friends")
        )

        self.assertEqual("users_foreign_key", posts_foreign_keys[0].get_name())
        self.assertEqual(
            ["friends_friend_id_foreign", "friends_user_id_foreign"],
            sorted([f.get_name() for f in friends_foreign_keys]),
        )

    def test_add_columns(self):
        with self.schema().table("posts") as table:
            table.text("content").nullable()
            table.integer("votes").default(QueryExpression(0))

        user = User.find(1)
        post = user.posts().order_by("id", "asc").first()

        self.assertEqual("User 1 Post 1", post.name)
        self.assertEqual(0, post.votes)

    def test_remove_columns(self):
        with self.schema().table("posts") as table:
            table.drop_column("name")

        self.assertRaises(
            ColumnDoesNotExist, self.connection().get_column, "posts", "name"
        )

        user = User.find(1)
        post = user.posts().order_by("id", "asc").first()

        self.assertFalse(hasattr(post, "name"))

    def test_rename_columns(self):
        old_foreign_keys = (
            self.connection().get_schema_manager().list_table_foreign_keys("posts")
        )

        with self.schema().table("posts") as table:
            table.rename_column("name", "title")

        self.assertRaises(
            ColumnDoesNotExist, self.connection().get_column, "posts", "name"
        )
        self.assertIsNotNone(self.connection().get_column("posts", "title"))

        foreign_keys = (
            self.connection().get_schema_manager().list_table_foreign_keys("posts")
        )

        self.assertEqual(len(foreign_keys), len(old_foreign_keys))

        user = User.find(1)
        post = user.posts().order_by("id", "asc").first()

        self.assertEqual("User 1 Post 1", post.title)

    def test_rename_columns_with_index(self):
        indexes = self.connection().get_schema_manager().list_table_indexes("users")
        old_foreign_keys = (
            self.connection().get_schema_manager().list_table_foreign_keys("posts")
        )

        index = indexes["users_email_unique"]
        self.assertEqual(["email"], index.get_columns())
        self.assertTrue(index.is_unique())

        with self.schema().table("users") as table:
            table.rename_column("email", "email_address")

        self.assertRaises(
            ColumnDoesNotExist, self.connection().get_column, "users", "email"
        )
        self.assertIsNotNone(self.connection().get_column("users", "email_address"))
        foreign_keys = (
            self.connection().get_schema_manager().list_table_foreign_keys("posts")
        )

        self.assertEqual(len(foreign_keys), len(old_foreign_keys))

        indexes = self.connection().get_schema_manager().list_table_indexes("users")

        index = indexes["users_email_unique"]
        self.assertEqual("users_email_unique", index.get_name())
        self.assertEqual(["email_address"], index.get_columns())
        self.assertTrue(index.is_unique())

    def test_rename_columns_with_foreign_keys(self):
        old_foreign_keys = (
            self.connection().get_schema_manager().list_table_foreign_keys("posts")
        )

        old_foreign_key = old_foreign_keys[0]
        self.assertEqual(["user_id"], old_foreign_key.get_local_columns())
        self.assertEqual(["id"], old_foreign_key.get_foreign_columns())
        self.assertEqual("users", old_foreign_key.get_foreign_table_name())

        with self.schema().table("posts") as table:
            table.rename_column("user_id", "my_user_id")

        self.assertRaises(
            ColumnDoesNotExist, self.connection().get_column, "posts", "user_id"
        )
        self.assertIsNotNone(self.connection().get_column("posts", "my_user_id"))
        foreign_keys = (
            self.connection().get_schema_manager().list_table_foreign_keys("posts")
        )

        self.assertEqual(len(foreign_keys), len(old_foreign_keys))

        foreign_key = foreign_keys[0]
        self.assertEqual(["my_user_id"], foreign_key.get_local_columns())
        self.assertEqual(["id"], foreign_key.get_foreign_columns())
        self.assertEqual("users", foreign_key.get_foreign_table_name())

    def test_change_columns(self):
        with self.schema().table("posts") as table:
            table.integer("votes").default(0)

        indexes = self.connection().get_schema_manager().list_table_indexes("posts")
        old_foreign_keys = (
            self.connection().get_schema_manager().list_table_foreign_keys("posts")
        )

        self.assertIn("posts_name_unique", indexes)
        self.assertEqual(["name"], indexes["posts_name_unique"].get_columns())
        self.assertTrue(indexes["posts_name_unique"].is_unique())

        post = Post.find(1)
        self.assertEqual(0, post.votes)

        with self.schema().table("posts") as table:
            table.string("name").nullable().change()
            table.string("votes").default("0").change()
            table.string("tag").default("new").change()

        name_column = self.connection().get_column("posts", "name")
        votes_column = self.connection().get_column("posts", "votes")
        status_column = self.connection().get_column("posts", "status")
        tag_column = self.connection().get_column("posts", "tag")
        self.assertFalse(name_column.get_notnull())
        self.assertTrue(votes_column.get_notnull())
        self.assertEqual("0", votes_column.get_default())

        self.assertFalse(status_column.get_notnull())
        self.assertEqual("draft", status_column.get_default())

        self.assertFalse(tag_column.get_notnull())
        self.assertEqual("new", tag_column.get_default())

        foreign_keys = (
            self.connection().get_schema_manager().list_table_foreign_keys("posts")
        )

        self.assertEqual(len(foreign_keys), len(old_foreign_keys))

        indexes = self.connection().get_schema_manager().list_table_indexes("posts")

        self.assertIn("posts_name_unique", indexes)
        self.assertEqual(["name"], indexes["posts_name_unique"].get_columns())
        self.assertTrue(indexes["posts_name_unique"].is_unique())

        post = Post.find(1)
        self.assertEqual("0", post.votes)

        with self.schema().table("users") as table:
            table.big_integer("votes").change()

    def test_cascading(self):
        user = User.create(email="john@doe.com")
        friend = User.create(email="jane@doe.com")
        another_friend = User.create(email="another@doe.com")
        user.friends().attach(friend)
        user.friends().attach(another_friend)

        user.delete()

        self.assertEqual(
            0, user.get_connection_resolver().connection().table("friends").count()
        )

        # Altering users table
        with self.schema().table("users") as table:
            table.string("email", 50).change()

        user = User.create(email="john@doe.com")
        user.friends().attach(friend)
        user.friends().attach(another_friend)

        user.delete()

        self.assertEqual(
            0, user.get_connection_resolver().connection().table("friends").count()
        )

    def grammar(self):
        return self.connection().get_default_query_grammar()

    def connection(self):
        return Model.get_connection_resolver().connection()

    def schema(self):
        return self.connection().get_schema_builder()


class User(Model):

    __guarded__ = []

    @belongs_to_many("friends", "user_id", "friend_id")
    def friends(self):
        return User

    @has_many("user_id")
    def posts(self):
        return Post

    @has_one("user_id")
    def post(self):
        return Post

    @morph_many("imageable")
    def photos(self):
        return Photo


class Post(Model):

    __guarded__ = []

    @belongs_to("user_id")
    def user(self):
        return User

    @morph_many("imageable")
    def photos(self):
        return Photo


class Photo(Model):

    __guarded__ = []

    @morph_to
    def imageable(self):
        return
