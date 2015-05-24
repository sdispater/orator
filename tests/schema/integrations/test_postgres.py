# -*- coding: utf-8 -*-

import os
from ... import OratorTestCase
from orator import Model
from orator.connections import PostgresConnection
from orator.connectors.postgres_connector import PostgresConnector
from orator.query.expression import QueryExpression


class SchemaBuilderPostgresIntegrationTestCase(OratorTestCase):

    @classmethod
    def setUpClass(cls):
        Model.set_connection_resolver(DatabaseIntegrationConnectionResolver())

    @classmethod
    def tearDownClass(cls):
        Model.unset_connection_resolver()

    def setUp(self):
        self.schema().drop_if_exists('photos')
        self.schema().drop_if_exists('posts')
        self.schema().drop_if_exists('friends')
        self.schema().drop_if_exists('users')

        with self.schema().create('users') as table:
            table.increments('id')
            table.string('email').unique()
            table.timestamps()

        with self.schema().create('friends') as table:
            table.integer('user_id')
            table.integer('friend_id')

            table.foreign('user_id').references('id').on('users')
            table.foreign('friend_id').references('id').on('users')

        with self.schema().create('posts') as table:
            table.increments('id')
            table.integer('user_id')
            table.string('name').unique()
            table.timestamps()

            table.foreign('user_id').references('id').on('users')

        with self.schema().create('photos') as table:
            table.increments('id')
            table.morphs('imageable')
            table.string('name')
            table.timestamps()

        self.connection().commit()

        for i in range(10):
            user = User.create(email='user%d@foo.com' % (i + 1))

            for j in range(10):
                post = Post(name='User %d Post %d' % (user.id, j + 1))
                user.posts().save(post)

    def tearDown(self):
        with self.schema().table('posts') as table:
            table.drop_foreign('posts_user_id_foreign')

        with self.schema().table('friends') as table:
            table.drop_foreign('friends_user_id_foreign')
            table.drop_foreign('friends_friend_id_foreign')

        self.schema().drop('users')
        self.schema().drop('friends')
        self.schema().drop('posts')
        self.schema().drop('photos')

    def test_add_columns(self):
        with self.schema().table('posts') as table:
            table.text('content').default('Test')
            table.integer('votes').default(QueryExpression(0))

        user = User.find(1)
        post = user.posts().order_by('id', 'asc').first()

        self.assertEqual('User 1 Post 1', post.name)
        self.assertEqual('Test', post.content)
        self.assertEqual(0, post.votes)

    def test_remove_columns(self):
        with self.schema().table('posts') as table:
            table.drop_column('name')

        self.assertIsNone(self.connection().get_column('posts', 'name'))

        user = User.find(1)
        post = user.posts().order_by('id', 'asc').first()

        self.assertFalse(hasattr(post, 'name'))

    def test_rename_columns(self):
        with self.schema().table('posts') as table:
            table.rename_column('name', 'title')

        self.assertIsNone(self.connection().get_column('posts', 'name'))
        self.assertIsNotNone(self.connection().get_column('posts', 'title'))

        user = User.find(1)
        post = user.posts().order_by('id', 'asc').first()

        self.assertEqual('User 1 Post 1', post.title)

    def test_rename_columns_with_index(self):
        with self.schema().table('users') as table:
            table.rename_column('email', 'email_address')

        self.assertIsNone(self.connection().get_column('users', 'email'))
        self.assertIsNotNone(self.connection().get_column('users', 'email_address'))

    def test_rename_columns_with_foreign_keys(self):
        with self.schema().table('posts') as table:
            table.rename_column('user_id', 'my_user_id')

        self.assertIsNone(self.connection().get_column('posts', 'user_id'))
        self.assertIsNotNone(self.connection().get_column('posts', 'my_user_id'))

    def test_change_columns(self):
        with self.schema().table('posts') as table:
            table.integer('votes').default(0)

        post = Post.find(1)
        self.assertEqual(0, post.votes)

        with self.schema().table('posts') as table:
            table.string('name').nullable().change()
            table.string('votes').default('0').change()

        name_column = self.connection().get_column('posts', 'name')
        votes_column = self.connection().get_column('posts', 'votes')
        self.assertFalse(name_column.get_notnull())
        self.assertTrue(votes_column.get_notnull())
        self.assertEqual('0', votes_column.get_default())

        post = Post.find(1)
        self.assertEqual('0', post.votes)

    def connection(self):
        return Model.get_connection_resolver().connection()

    def schema(self):
        """
        :rtype: orator.schema.SchemaBuilder
        """
        return self.connection().get_schema_builder()


class User(Model):

    __guarded__ = []

    @property
    def friends(self):
        return self.belongs_to_many(User, 'friends', 'user_id', 'friend_id')

    @property
    def posts(self):
        return self.has_many(Post, 'user_id')

    @property
    def post(self):
        return self.has_one(Post, 'user_id')

    @property
    def photos(self):
        return self.morph_many(Photo, 'imageable')


class Post(Model):

    __guarded__ = []

    @property
    def user(self):
        return self.belongs_to(User, 'user_id')

    @property
    def photos(self):
        return self.morph_many(Photo, 'imageable')


class Photo(Model):

    __guarded__ = []

    @property
    def imageable(self):
        return self.morph_to()


class DatabaseIntegrationConnectionResolver(object):

    _connection = None

    def connection(self, name=None):
        if self._connection:
            return self._connection

        database = os.environ.get('ORATOR_POSTGRES_TEST_DATABASE', 'orator_test')
        user = os.environ.get('ORATOR_POSTGRES_TEST_USER', 'postgres')
        password = os.environ.get('ORATOR_POSTGRES_TEST_PASSWORD', None)

        self._connection = PostgresConnection(
            PostgresConnector().connect({
                'database': database,
                'user': user,
                'password': password
            })
        )

        return self._connection

    def get_default_connection(self):
        return 'default'

    def set_default_connection(self, name):
        pass
