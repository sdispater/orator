# -*- coding: utf-8 -*-

from ... import OratorTestCase
from orator import DatabaseManager, SoftDeletes, Model
from orator.orm import has_many
from orator.query import QueryBuilder
from orator.pagination import Paginator


class SoftDeletesIntegrationTestCase(OratorTestCase):

    databases = {"test": {"driver": "sqlite", "database": ":memory:"}}

    def setUp(self):
        self.db = DatabaseManager(self.databases)

        Model.set_connection_resolver(self.db)

        self.create_schema()

    def create_schema(self):
        with self.schema().create("users") as table:
            table.increments("id")
            table.string("email").unique()
            table.timestamps()
            table.soft_deletes()

        with self.schema().create("posts") as table:
            table.increments("id")
            table.string("title")
            table.integer("user_id")
            table.timestamps()
            table.soft_deletes()

        with self.schema().create("comments") as table:
            table.increments("id")
            table.string("body")
            table.integer("post_id")
            table.timestamps()
            table.soft_deletes()

    def tearDown(self):
        self.schema().drop("users")
        self.schema().drop("posts")
        self.schema().drop("comments")

        Model.unset_connection_resolver()

    def test_soft_deletes_are_not_retrieved(self):
        self.create_users()

        users = SoftDeletesTestUser.all()

        self.assertEqual(1, len(users))
        self.assertEqual(2, users.first().id)
        self.assertIsNone(SoftDeletesTestUser.find(1))

    def test_soft_deletes_are_not_retrieved_from_base_query(self):
        self.create_users()

        query = SoftDeletesTestUser.query().to_base()

        self.assertIsInstance(query, QueryBuilder)
        self.assertEqual(1, len(query.get()))

    def test_soft_deletes_are_not_retrieved_from_builder_helpers(self):
        self.create_users()

        count = 0
        query = SoftDeletesTestUser.query()
        for users in query.chunk(2):
            count += len(users)

        self.assertEqual(1, count)

        query = SoftDeletesTestUser.query()
        self.assertEqual(1, len(query.lists("email")))

        Paginator.current_page_resolver(lambda: 1)
        query = SoftDeletesTestUser.query()
        self.assertEqual(1, len(query.paginate(2).items))

        Paginator.current_page_resolver(lambda: 1)
        query = SoftDeletesTestUser.query()
        self.assertEqual(1, len(query.simple_paginate(2).items))

        self.assertEqual(
            0, SoftDeletesTestUser.where("email", "john@doe.com").increment("id")
        )
        self.assertEqual(
            0, SoftDeletesTestUser.where("email", "john@doe.com").decrement("id")
        )

    def test_with_trashed_returns_all_records(self):
        self.create_users()

        self.assertEqual(2, SoftDeletesTestUser.with_trashed().get().count())
        self.assertIsInstance(
            SoftDeletesTestUser.with_trashed().find(1), SoftDeletesTestUser
        )

    def test_delete_sets_deleted_column(self):
        self.create_users()

        self.assertIsNotNone(SoftDeletesTestUser.with_trashed().find(1).deleted_at)
        self.assertIsNone(SoftDeletesTestUser.find(2).deleted_at)

    def test_force_delete_actually_deletes_records(self):
        self.create_users()

        SoftDeletesTestUser.find(2).force_delete()

        users = SoftDeletesTestUser.with_trashed().get()

        self.assertEqual(1, len(users))
        self.assertEqual(1, users.first().id)

    def test_restore_restores_records(self):
        self.create_users()

        john = SoftDeletesTestUser.with_trashed().find(1)

        self.assertTrue(john.trashed())

        john.restore()

        users = SoftDeletesTestUser.all()

        self.assertEqual(2, len(users))
        self.assertIsNone(SoftDeletesTestUser.find(1).deleted_at)
        self.assertIsNone(SoftDeletesTestUser.find(2).deleted_at)

    def test_only_trashed_only_returns_trashed_records(self):
        self.create_users()

        users = SoftDeletesTestUser.only_trashed().get()

        self.assertEqual(1, len(users))
        self.assertEqual(1, users.first().id)

    def test_first_or_new_ignores_soft_deletes(self):
        self.create_users()

        john = SoftDeletesTestUser.first_or_new(id=1)
        self.assertEqual("john@doe.com", john.email)

    def test_where_has_with_deleted_relationship(self):
        self.create_users()

        jane = SoftDeletesTestUser.where("email", "jane@doe.com").first()
        post = jane.posts().create(title="First Title")

        users = SoftDeletesTestUser.where("email", "john@doe.com").has("posts").get()
        self.assertEqual(0, len(users))

        users = SoftDeletesTestUser.where("email", "jane@doe.com").has("posts").get()
        self.assertEqual(1, len(users))

        users = (
            SoftDeletesTestUser.where("email", "doesnt@exist.com").or_has("posts").get()
        )
        self.assertEqual(1, len(users))

        users = SoftDeletesTestUser.where_has(
            "posts", lambda q: q.where("title", "First Title")
        ).get()
        self.assertEqual(1, len(users))

        users = SoftDeletesTestUser.where_has(
            "posts", lambda q: q.where("title", "Another Title")
        ).get()
        self.assertEqual(0, len(users))

        users = (
            SoftDeletesTestUser.where("email", "doesnt@exist.com")
            .or_where_has("posts", lambda q: q.where("title", "First Title"))
            .get()
        )
        self.assertEqual(1, len(users))

        # With post delete
        post.delete()
        users = SoftDeletesTestUser.has("posts").get()
        self.assertEqual(0, len(users))

    def test_where_has_with_nested_deleted_relationship(self):
        self.create_users()

        jane = SoftDeletesTestUser.where("email", "jane@doe.com").first()
        post = jane.posts().create(title="First Title")
        comment = post.comments().create(body="Comment Body")
        comment.delete()

        users = SoftDeletesTestUser.has("posts.comments").get()
        self.assertEqual(0, len(users))

        users = SoftDeletesTestUser.doesnt_have("posts.comments").get()
        self.assertEqual(1, len(users))

    def test_or_where_with_soft_deletes_constraint(self):
        self.create_users()

        users = SoftDeletesTestUser.where("email", "john@doe.com").or_where(
            "email", "jane@doe.com"
        )
        self.assertEqual(1, len(users.get()))
        self.assertEqual(["jane@doe.com"], users.order_by("id").lists("email"))

    def test_where_exists_on_soft_delete_model(self):
        self.create_users()

        users = SoftDeletesTestUser.where_exists(
            SoftDeletesTestUser.where("email", "jane@doe.com")
        )

        self.assertEqual(1, len(users.get()))
        self.assertEqual(["jane@doe.com"], users.order_by("id").lists("email"))

    def create_users(self):
        john = SoftDeletesTestUser.create(email="john@doe.com")
        jane = SoftDeletesTestUser.create(email="jane@doe.com")

        john.delete()

    def connection(self):
        return self.db.connection()

    def schema(self):
        return self.connection().get_schema_builder()


class SoftDeletesTestUser(SoftDeletes, Model):

    __table__ = "users"

    __dates__ = ["deleted_at"]

    __guarded__ = []

    @has_many
    def posts(self):
        return SoftDeletesTestPost


class SoftDeletesTestPost(SoftDeletes, Model):

    __table__ = "posts"

    __dates__ = ["deleted_at"]

    __guarded__ = []

    @has_many
    def comments(self):
        return SoftDeletesTestComment


class SoftDeletesTestComment(SoftDeletes, Model):

    __table__ = "comments"

    __dates__ = ["deleted_at"]

    __guarded__ = []
