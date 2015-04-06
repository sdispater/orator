# -*- coding: utf-8 -*-

import sqlite3
from . import EloquentTestCase
from eloquent import Model
from eloquent.connections import SQLiteConnection
from eloquent.connectors.sqlite_connector import SQLiteConnector


class EloquentIntegrationTestCase(EloquentTestCase):

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
            table.timestamps()

        with self.schema().create('friends') as table:
            table.integer('user_id')
            table.integer('friend_id')

        with self.schema().create('posts') as table:
            table.increments('id')
            table.integer('user_id')
            table.string('name')
            table.timestamps()

        with self.schema().create('photos') as table:
            table.increments('id')
            table.morphs('imageable')
            table.string('name')
            table.timestamps()

    def tearDown(self):
        self.schema().drop('users')
        self.schema().drop('friends')
        self.schema().drop('posts')
        self.schema().drop('photos')

    def test_basic_model_retrieval(self):
        EloquentTestUser.create(email='john@doe.com')
        model = EloquentTestUser.where('email', 'john@doe.com').first()
        self.assertEqual('john@doe.com', model.email)

    def connection(self):
        return Model.get_connection_resolver().connection()

    def schema(self):
        return self.connection().get_schema_builder()


class EloquentTestUser(Model):

    __table__ = 'users'
    __guarded__ = []

    @property
    def friends(self):
        return self.belongs_to_many(EloquentTestUser, 'friends', 'user_id', 'friend_id')

    @property
    def posts(self):
        return self.has_many(EloquentTestPost, 'user_id')

    @property
    def post(self):
        return self.has_one(EloquentTestPost, 'user_id')

    @property
    def photos(self):
        return self.morph_many(EloquentTestPhoto, 'imageable')


class EloquentTestPost(Model):

    __table__ = 'posts'
    __guarded__ = []

    @property
    def user(self):
        return self.belongs_to(EloquentTestUser, 'user_id')

    @property
    def photos(self):
        return self.morph_many(EloquentTestPhoto, 'imageable')


class EloquentTestPhoto(Model):

    __table__ = 'photos'
    __guarded__ = []

    @property
    def imageable(self):
        return self.morph_to()


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
