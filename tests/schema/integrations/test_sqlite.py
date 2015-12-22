# -*- coding: utf-8 -*-

from ... import OratorTestCase
from orator import Model
from orator.orm import has_one, has_many, belongs_to, belongs_to_many, morph_to, morph_many
from orator.connections import SQLiteConnection
from orator.connectors.sqlite_connector import SQLiteConnector
from orator.query.expression import QueryExpression


class SchemaBuilderSQLiteIntegrationTestCase(OratorTestCase):

    @classmethod
    def setUpClass(cls):
        Model.set_connection_resolver(DatabaseIntegrationConnectionResolver())

    @classmethod
    def tearDownClass(cls):
        Model.unset_connection_resolver()

    def setUp(self):
        with self.schema().create('users') as table:
            table.increments('id')
            table.string('email').unique()
            table.integer('votes').default(0)
            table.timestamps()

        with self.schema().create('friends') as table:
            table.integer('user_id')
            table.integer('friend_id')

            table.foreign('user_id').references('id').on('users').on_delete('cascade')
            table.foreign('friend_id').references('id').on('users').on_delete('cascade')

        with self.schema().create('posts') as table:
            table.increments('id')
            table.integer('user_id')
            table.string('name').unique()
            table.string('status').default('draft').nullable()
            table.string('default').default(0)
            table.timestamps()

            table.foreign('user_id').references('id').on('users')

        with self.schema().create('photos') as table:
            table.increments('id')
            table.morphs('imageable')
            table.string('name')
            table.timestamps()

        for i in range(10):
            user = User.create(email='user%d@foo.com' % (i + 1))

            for j in range(10):
                post = Post(name='User %d Post %d' % (user.id, j + 1))
                user.posts().save(post)

    def tearDown(self):
        self.schema().drop('photos')
        self.schema().drop('posts')
        self.schema().drop('friends')
        self.schema().drop('users')

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
        old_foreign_keys = self.connection().get_schema_manager().list_table_foreign_keys('posts')

        with self.schema().table('posts') as table:
            table.rename_column('name', 'title')

        self.assertIsNone(self.connection().get_column('posts', 'name'))
        self.assertIsNotNone(self.connection().get_column('posts', 'title'))

        foreign_keys = self.connection().get_schema_manager().list_table_foreign_keys('posts')

        self.assertEqual(len(foreign_keys), len(old_foreign_keys))

        user = User.find(1)
        post = user.posts().order_by('id', 'asc').first()

        self.assertEqual('User 1 Post 1', post.title)

    def test_rename_columns_with_index(self):
        indexes = self.connection().get_schema_manager().list_table_indexes('users')
        old_foreign_keys = self.connection().get_schema_manager().list_table_foreign_keys('posts')

        self.assertEqual('users_email_unique', indexes[0]['name'])
        self.assertEqual(['email'], indexes[0]['columns'])
        self.assertTrue(indexes[0]['unique'])

        with self.schema().table('users') as table:
            table.rename_column('email', 'email_address')

        self.assertIsNone(self.connection().get_column('users', 'email'))
        self.assertIsNotNone(self.connection().get_column('users', 'email_address'))
        foreign_keys = self.connection().get_schema_manager().list_table_foreign_keys('posts')

        self.assertEqual(len(foreign_keys), len(old_foreign_keys))

        indexes = self.connection().get_schema_manager().list_table_indexes('users')

        self.assertEqual('users_email_address_unique', indexes[0]['name'])
        self.assertEqual(['email_address'], indexes[0]['columns'])
        self.assertTrue(indexes[0]['unique'])

    def test_rename_columns_with_foreign_keys(self):
        old_foreign_keys = self.connection().get_schema_manager().list_table_foreign_keys('posts')

        self.assertEqual('user_id', old_foreign_keys[0]['from'])
        self.assertEqual('id', old_foreign_keys[0]['to'])
        self.assertEqual('users', old_foreign_keys[0]['table'])

        with self.schema().table('posts') as table:
            table.rename_column('user_id', 'my_user_id')

        self.assertIsNone(self.connection().get_column('posts', 'user_id'))
        self.assertIsNotNone(self.connection().get_column('posts', 'my_user_id'))
        foreign_keys = self.connection().get_schema_manager().list_table_foreign_keys('posts')

        self.assertEqual(len(foreign_keys), len(old_foreign_keys))

        self.assertEqual('my_user_id', foreign_keys[0]['from'])
        self.assertEqual('id', foreign_keys[0]['to'])
        self.assertEqual('users', foreign_keys[0]['table'])

    def test_change_columns(self):
        with self.schema().table('posts') as table:
            table.integer('votes').default(0)

        indexes = self.connection().get_schema_manager().list_table_indexes('posts')
        old_foreign_keys = self.connection().get_schema_manager().list_table_foreign_keys('posts')

        self.assertEqual('posts_name_unique', indexes[0]['name'])
        self.assertEqual(['name'], indexes[0]['columns'])
        self.assertTrue(indexes[0]['unique'])

        post = Post.find(1)
        self.assertEqual(0, post.votes)

        with self.schema().table('posts') as table:
            table.string('name').nullable().change()
            table.string('votes').default('0').change()

        name_column = self.connection().get_column('posts', 'name')
        votes_column = self.connection().get_column('posts', 'votes')
        status_column = self.connection().get_column('posts', 'status')
        self.assertFalse(name_column.get_notnull())
        self.assertTrue(votes_column.get_notnull())
        self.assertEqual("0", votes_column.get_default())

        self.assertFalse(status_column.get_notnull())
        self.assertEqual("draft", status_column.get_default())

        foreign_keys = self.connection().get_schema_manager().list_table_foreign_keys('posts')

        self.assertEqual(len(foreign_keys), len(old_foreign_keys))

        indexes = self.connection().get_schema_manager().list_table_indexes('posts')

        self.assertEqual('posts_name_unique', indexes[0]['name'])
        self.assertEqual(['name'], indexes[0]['columns'])
        self.assertTrue(indexes[0]['unique'])

        post = Post.find(1)
        self.assertEqual('0', post.votes)

        with self.schema().table('users') as table:
            table.big_integer('votes').change()

    def test_cascading(self):
        user = User.create(email='john@doe.com')
        friend = User.create(email='jane@doe.com')
        another_friend = User.create(email='another@doe.com')
        user.friends().attach(friend)
        user.friends().attach(another_friend)

        user.delete()

        self.assertEqual(0, user.get_connection_resolver().connection().table('friends').count())

    def connection(self):
        return Model.get_connection_resolver().connection()

    def schema(self):
        return self.connection().get_schema_builder()


class SchemaBuilderSQLiteIntegrationCascadingTestCase(OratorTestCase):

    @classmethod
    def setUpClass(cls):
        Model.set_connection_resolver(DatabaseIntegrationConnectionWithoutForeignKeysResolver())

    @classmethod
    def tearDownClass(cls):
        Model.unset_connection_resolver()

    def setUp(self):
        with self.schema().create('users') as table:
            table.increments('id')
            table.string('email').unique()
            table.timestamps()

        with self.schema().create('friends') as table:
            table.integer('user_id')
            table.integer('friend_id')

            table.foreign('user_id').references('id').on('users').on_delete('cascade')
            table.foreign('friend_id').references('id').on('users').on_delete('cascade')

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

        for i in range(10):
            user = User.create(email='user%d@foo.com' % (i + 1))

            for j in range(10):
                post = Post(name='User %d Post %d' % (user.id, j + 1))
                user.posts().save(post)

    def tearDown(self):
        self.schema().drop('photos')
        self.schema().drop('posts')
        self.schema().drop('friends')
        self.schema().drop('users')

    def test_cascading(self):
        user = User.create(email='john@doe.com')
        friend = User.create(email='jane@doe.com')
        another_friend = User.create(email='another@doe.com')
        user.friends().attach(friend)
        user.friends().attach(another_friend)

        user.delete()

        self.assertEqual(2, user.get_connection_resolver().connection().table('friends').count())

    def connection(self):
        return Model.get_connection_resolver().connection()

    def schema(self):
        return self.connection().get_schema_builder()


class User(Model):

    __guarded__ = []

    @belongs_to_many('friends', 'user_id', 'friend_id')
    def friends(self):
        return User

    @has_many('user_id')
    def posts(self):
        return Post

    @has_one('user_id')
    def post(self):
        return Post

    @morph_many('imageable')
    def photos(self):
        return Photo


class Post(Model):

    __guarded__ = []

    @belongs_to('user_id')
    def user(self):
        return User

    @morph_many('imageable')
    def photos(self):
        return Photo


class Photo(Model):

    __guarded__ = []

    @morph_to
    def imageable(self):
        return


class DatabaseIntegrationConnectionResolver(object):

    _connection = None

    def connection(self, name=None):
        if self._connection:
            return self._connection

        self._connection = SQLiteConnection(SQLiteConnector().connect({'database': ':memory:'}))

        return self._connection

    def get_default_connection(self):
        return 'default'

    def set_default_connection(self, name):
        pass


class DatabaseIntegrationConnectionWithoutForeignKeysResolver(DatabaseIntegrationConnectionResolver):

    _connection = None

    def connection(self, name=None):
        if self._connection:
            return self._connection

        self._connection = SQLiteConnection(
            SQLiteConnector().connect(
                {'database': ':memory:',
                 'foreign_keys': False}
            )
        )

        return self._connection
