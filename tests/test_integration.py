# -*- coding: utf-8 -*-

import arrow
from . import EloquentTestCase
from eloquent import Model, Collection
from eloquent.connections import SQLiteConnection
from eloquent.connectors.sqlite_connector import SQLiteConnector
from eloquent.exceptions.orm import ModelNotFound


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

    def test_basic_model_collection_retrieval(self):
        EloquentTestUser.create(id=1, email='john@doe.com')
        EloquentTestUser.create(id=2, email='jane@doe.com')

        models = EloquentTestUser.oldest('id').get()

        self.assertEqual(2, len(models))
        self.assertIsInstance(models, Collection)
        self.assertIsInstance(models[0], EloquentTestUser)
        self.assertIsInstance(models[1], EloquentTestUser)
        self.assertEqual('john@doe.com', models[0].email)
        self.assertEqual('jane@doe.com', models[1].email)

    def test_lists_retrieval(self):
        EloquentTestUser.create(id=1, email='john@doe.com')
        EloquentTestUser.create(id=2, email='jane@doe.com')

        simple = EloquentTestUser.oldest('id').lists('email')
        keyed = EloquentTestUser.oldest('id').lists('email', 'id')

        self.assertEqual(['john@doe.com', 'jane@doe.com'], simple)
        self.assertEqual({1: 'john@doe.com', 2: 'jane@doe.com'}, keyed)

    def test_find_or_fail(self):
        EloquentTestUser.create(id=1, email='john@doe.com')
        EloquentTestUser.create(id=2, email='jane@doe.com')

        single = EloquentTestUser.find_or_fail(1)
        multiple = EloquentTestUser.find_or_fail([1, 2])

        self.assertIsInstance(single, EloquentTestUser)
        self.assertEqual('john@doe.com', single.email)
        self.assertIsInstance(multiple, Collection)
        self.assertIsInstance(multiple[0], EloquentTestUser)
        self.assertIsInstance(multiple[1], EloquentTestUser)

    def test_find_or_fail_with_single_id_raises_model_not_found_exception(self):
        self.assertRaises(
            ModelNotFound,
            EloquentTestUser.find_or_fail,
            1
        )

    def test_find_or_fail_with_multiple_ids_raises_model_not_found_exception(self):
        self.assertRaises(
            ModelNotFound,
            EloquentTestUser.find_or_fail,
            [1, 2]
        )

    def test_one_to_one_relationship(self):
        user = EloquentTestUser.create(email='john@doe.com')
        user.post().create(name='First Post')

        post = user.post
        user = post.user

        self.assertEqual('john@doe.com', user.email)
        self.assertEqual('First Post', post.name)

    def test_one_to_many_relationship(self):
        user = EloquentTestUser.create(email='john@doe.com')
        user.posts().create(name='First Post')
        user.posts().create(name='Second Post')

        posts = user.posts
        post2 = user.posts().where('name', 'Second Post').first()

        self.assertEqual(2, len(posts))
        #self.assertIsInstance(posts[0], EloquentTestPost)
        #self.assertIsInstance(posts[1], EloquentTestPost)
        #self.assertIsInstance(post2, EloquentTestPost)
        self.assertEqual('Second Post', post2.name)
        #self.assertIsInstance(post2.user.instance, EloquentTestUser)
        self.assertEqual('john@doe.com', post2.user.email)

    def test_basic_model_hydrate(self):
        EloquentTestUser.create(id=1, email='john@doe.com')
        EloquentTestUser.create(id=2, email='jane@doe.com')

        models = EloquentTestUser.hydrate_raw(
            'SELECT * FROM users WHERE email = ?',
            ['jane@doe.com'],
            'foo_connection'
        )
        self.assertIsInstance(models, Collection)
        self.assertIsInstance(models[0], EloquentTestUser)
        self.assertEqual('jane@doe.com', models[0].email)
        self.assertEqual('foo_connection', models[0].get_connection_name())
        self.assertEqual(1, len(models))

    def test_has_on_self_referencing_belongs_to_many_relationship(self):
        user = EloquentTestUser.create(id=1, email='john@doe.com')
        friend = user.friends().create(email='jane@doe.com')

        results = EloquentTestUser.has('friends').get()

        self.assertEqual(1, len(results))
        self.assertEqual('john@doe.com', results.first().email)

    def test_basic_has_many_eager_loading(self):
        user = EloquentTestUser.create(id=1, email='john@doe.com')
        user.posts().create(name='First Post')
        user = EloquentTestUser.with_('posts').where('email', 'john@doe.com').first()

        self.assertEqual('First Post', user.posts.first().name)

        post = EloquentTestPost.with_('user').where('name', 'First Post').get()
        self.assertEqual('john@doe.com', post.first().user.email)

    def test_basic_morph_many_relationship(self):
        user = EloquentTestUser.create(id=1, email='john@doe.com')
        user.photos().create(name='Avatar 1')
        user.photos().create(name='Avatar 2')
        post = user.posts().create(name='First Post')
        post.photos().create(name='Hero 1')
        post.photos().create(name='Hero 2')

        self.assertIsInstance(user.photos.instance, Collection)
        #self.assertIsInstance(user.photos[0], EloquentTestPhoto)
        self.assertIsInstance(post.photos.instance, Collection)
        #self.assertIsInstance(post.photos[0], EloquentTestPhoto)
        self.assertEqual(2, len(user.photos))
        self.assertEqual(2, len(post.photos))
        self.assertEqual('Avatar 1', user.photos[0].name)
        self.assertEqual('Avatar 2', user.photos[1].name)
        self.assertEqual('Hero 1', post.photos[0].name)
        self.assertEqual('Hero 2', post.photos[1].name)

        photos = EloquentTestPhoto.order_by('name').get()

        self.assertIsInstance(photos, Collection)
        self.assertEqual(4, len(photos))
        #self.assertIsInstance(photos[0].imageable.instance, EloquentTestUser)
        #self.assertIsInstance(photos[2].imageable.instance, EloquentTestPost)
        self.assertEqual('john@doe.com', photos[1].imageable.email)
        self.assertEqual('First Post', photos[3].imageable.name)

    def test_multi_insert_with_different_values(self):
        date = arrow.utcnow().naive
        result = EloquentTestPost.insert([
            {
                'user_id': 1, 'name': 'Post', 'created_at': date, 'updated_at': date
            }, {
                'user_id': 2, 'name': 'Post', 'created_at': date, 'updated_at': date
            }
        ])

        self.assertTrue(result)
        self.assertEqual(2, EloquentTestPost.count())

    def test_multi_insert_with_same_values(self):
        date = arrow.utcnow().naive
        result = EloquentTestPost.insert([
            {
                'user_id': 1, 'name': 'Post', 'created_at': date, 'updated_at': date
            }, {
                'user_id': 1, 'name': 'Post', 'created_at': date, 'updated_at': date
            }
        ])

        self.assertTrue(result)
        self.assertEqual(2, EloquentTestPost.count())

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
        return self.has_many('posts', 'user_id')

    @property
    def post(self):
        return self.has_one(EloquentTestPost, 'user_id')

    @property
    def photos(self):
        return self.morph_many('photos', 'imageable')


class EloquentTestPost(Model):

    __table__ = 'posts'
    __guarded__ = []

    @property
    def user(self):
        return self.belongs_to(EloquentTestUser, 'user_id')

    @property
    def photos(self):
        return self.morph_many('photos', 'imageable')


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
