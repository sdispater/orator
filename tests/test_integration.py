# -*- coding: utf-8 -*-

import arrow
from . import OratorTestCase
from orator import Model, Collection
from orator.connections import SQLiteConnection
from orator.connectors.sqlite_connector import SQLiteConnector
from orator.exceptions.orm import ModelNotFound
from orator.orm.relations.relation import RelationWrapper


class OratorIntegrationTestCase(OratorTestCase):

    @classmethod
    def setUpClass(cls):
        Model.set_connection_resolver(DatabaseIntegrationConnectionResolver())

    @classmethod
    def tearDownClass(cls):
        Model.unset_connection_resolver()

    def setUp(self):
        with self.schema().create('test_users') as table:
            table.increments('id')
            table.string('email').unique()
            table.timestamps()

        with self.schema().create('test_friends') as table:
            table.increments('id')
            table.integer('user_id')
            table.integer('friend_id')

        with self.schema().create('test_posts') as table:
            table.increments('id')
            table.integer('user_id')
            table.string('name')
            table.timestamps()

        with self.schema().create('test_photos') as table:
            table.increments('id')
            table.morphs('imageable')
            table.string('name')
            table.timestamps()

    def tearDown(self):
        self.schema().drop('test_users')
        self.schema().drop('test_friends')
        self.schema().drop('test_posts')
        self.schema().drop('test_photos')

    def test_basic_model_retrieval(self):
        OratorTestUser.create(email='john@doe.com')
        model = OratorTestUser.where('email', 'john@doe.com').first()
        self.assertEqual('john@doe.com', model.email)

    def test_basic_model_collection_retrieval(self):
        OratorTestUser.create(id=1, email='john@doe.com')
        OratorTestUser.create(id=2, email='jane@doe.com')

        models = OratorTestUser.oldest('id').get()

        self.assertEqual(2, len(models))
        self.assertIsInstance(models, Collection)
        self.assertIsInstance(models[0], OratorTestUser)
        self.assertIsInstance(models[1], OratorTestUser)
        self.assertEqual('john@doe.com', models[0].email)
        self.assertEqual('jane@doe.com', models[1].email)

    def test_lists_retrieval(self):
        OratorTestUser.create(id=1, email='john@doe.com')
        OratorTestUser.create(id=2, email='jane@doe.com')

        simple = OratorTestUser.oldest('id').lists('email')
        keyed = OratorTestUser.oldest('id').lists('email', 'id')

        self.assertEqual(['john@doe.com', 'jane@doe.com'], simple)
        self.assertEqual({1: 'john@doe.com', 2: 'jane@doe.com'}, keyed)

    def test_find_or_fail(self):
        OratorTestUser.create(id=1, email='john@doe.com')
        OratorTestUser.create(id=2, email='jane@doe.com')

        single = OratorTestUser.find_or_fail(1)
        multiple = OratorTestUser.find_or_fail([1, 2])

        self.assertIsInstance(single, OratorTestUser)
        self.assertEqual('john@doe.com', single.email)
        self.assertIsInstance(multiple, Collection)
        self.assertIsInstance(multiple[0], OratorTestUser)
        self.assertIsInstance(multiple[1], OratorTestUser)

    def test_find_or_fail_with_single_id_raises_model_not_found_exception(self):
        self.assertRaises(
            ModelNotFound,
            OratorTestUser.find_or_fail,
            1
        )

    def test_find_or_fail_with_multiple_ids_raises_model_not_found_exception(self):
        self.assertRaises(
            ModelNotFound,
            OratorTestUser.find_or_fail,
            [1, 2]
        )

    def test_one_to_one_relationship(self):
        user = OratorTestUser.create(email='john@doe.com')
        user.post().create(name='First Post')

        post = user.post
        user = post.user

        self.assertEqual('john@doe.com', user.email)
        self.assertEqual('First Post', post.name)

    def test_one_to_many_relationship(self):
        user = OratorTestUser.create(email='john@doe.com')
        user.posts().create(name='First Post')
        user.posts().create(name='Second Post')

        posts = user.posts
        post2 = user.posts().where('name', 'Second Post').first()

        self.assertEqual(2, len(posts))
        #self.assertIsInstance(posts[0], OratorTestPost)
        #self.assertIsInstance(posts[1], OratorTestPost)
        #self.assertIsInstance(post2, OratorTestPost)
        self.assertEqual('Second Post', post2.name)
        #self.assertIsInstance(post2.user.instance, OratorTestUser)
        self.assertEqual('john@doe.com', post2.user.email)

    def test_basic_model_hydrate(self):
        OratorTestUser.create(id=1, email='john@doe.com')
        OratorTestUser.create(id=2, email='jane@doe.com')

        models = OratorTestUser.hydrate_raw(
            'SELECT * FROM test_users WHERE email = ?',
            ['jane@doe.com'],
            'foo_connection'
        )
        self.assertIsInstance(models, Collection)
        self.assertIsInstance(models[0], OratorTestUser)
        self.assertEqual('jane@doe.com', models[0].email)
        self.assertEqual('foo_connection', models[0].get_connection_name())
        self.assertEqual(1, len(models))

    def test_has_on_self_referencing_belongs_to_many_relationship(self):
        user = OratorTestUser.create(id=1, email='john@doe.com')
        friend = user.friends().create(email='jane@doe.com')

        results = OratorTestUser.has('friends').get()

        self.assertEqual(1, len(results))
        self.assertEqual('john@doe.com', results.first().email)

    def test_basic_has_many_eager_loading(self):
        user = OratorTestUser.create(id=1, email='john@doe.com')
        user.posts().create(name='First Post')
        user = OratorTestUser.with_('posts').where('email', 'john@doe.com').first()

        self.assertEqual('First Post', user.posts.first().name)

        post = OratorTestPost.with_('user').where('name', 'First Post').get()
        self.assertEqual('john@doe.com', post.first().user.email)

    def test_basic_morph_many_relationship(self):
        user = OratorTestUser.create(id=1, email='john@doe.com')
        user.photos().create(name='Avatar 1')
        user.photos().create(name='Avatar 2')
        post = user.posts().create(name='First Post')
        post.photos().create(name='Hero 1')
        post.photos().create(name='Hero 2')

        self.assertIsInstance(user.photos, Collection)
        #self.assertIsInstance(user.photos[0], OratorTestPhoto)
        self.assertIsInstance(post.photos, Collection)
        #self.assertIsInstance(post.photos[0], OratorTestPhoto)
        self.assertEqual(2, len(user.photos))
        self.assertEqual(2, len(post.photos))
        self.assertEqual('Avatar 1', user.photos[0].name)
        self.assertEqual('Avatar 2', user.photos[1].name)
        self.assertEqual('Hero 1', post.photos[0].name)
        self.assertEqual('Hero 2', post.photos[1].name)

        photos = OratorTestPhoto.order_by('name').get()

        self.assertIsInstance(photos, Collection)
        self.assertEqual(4, len(photos))
        #self.assertIsInstance(photos[0].imageable.instance, OratorTestUser)
        #self.assertIsInstance(photos[2].imageable.instance, OratorTestPost)
        self.assertEqual('john@doe.com', photos[1].imageable.email)
        self.assertEqual('First Post', photos[3].imageable.name)

    def test_multi_insert_with_different_values(self):
        date = arrow.utcnow().naive
        result = OratorTestPost.insert([
            {
                'user_id': 1, 'name': 'Post', 'created_at': date, 'updated_at': date
            }, {
                'user_id': 2, 'name': 'Post', 'created_at': date, 'updated_at': date
            }
        ])

        self.assertTrue(result)
        self.assertEqual(2, OratorTestPost.count())

    def test_multi_insert_with_same_values(self):
        date = arrow.utcnow().naive
        result = OratorTestPost.insert([
            {
                'user_id': 1, 'name': 'Post', 'created_at': date, 'updated_at': date
            }, {
                'user_id': 1, 'name': 'Post', 'created_at': date, 'updated_at': date
            }
        ])

        self.assertTrue(result)
        self.assertEqual(2, OratorTestPost.count())

    def test_belongs_to_many_further_query(self):
        user = OratorTestUser.create(id=1, email='john@doe.com')
        friend = OratorTestUser.create(id=2, email='jane@doe.com')
        another_friend = OratorTestUser.create(id=3, email='another@doe.com')
        user.friends().attach(friend)
        user.friends().attach(another_friend)
        related_friend = OratorTestUser.with_('friends').find(1).friends().where('test_users.id', 3).first()

        self.assertEqual(3, related_friend.id)
        self.assertEqual('another@doe.com', related_friend.email)
        self.assertIn('pivot', related_friend.to_dict())
        self.assertEqual(1, related_friend.pivot.user_id)
        self.assertEqual(3, related_friend.pivot.friend_id)
        self.assertTrue(hasattr(related_friend.pivot, 'id'))

        self.assertIsInstance(user.friends().with_pivot('id'), RelationWrapper)

    def connection(self):
        return Model.get_connection_resolver().connection()

    def schema(self):
        return self.connection().get_schema_builder()


class OratorTestUser(Model):

    __table__ = 'test_users'
    __guarded__ = []

    @property
    def friends(self):
        return self.belongs_to_many(
            OratorTestUser,
            'test_friends',
            'user_id',
            'friend_id'
        ).with_pivot('id')

    @property
    def posts(self):
        return self.has_many('test_posts', 'user_id')

    @property
    def post(self):
        return self.has_one(OratorTestPost, 'user_id')

    @property
    def photos(self):
        return self.morph_many('test_photos', 'imageable')


class OratorTestPost(Model):

    __table__ = 'test_posts'
    __guarded__ = []

    @property
    def user(self):
        return self.belongs_to(OratorTestUser, 'user_id')

    @property
    def photos(self):
        return self.morph_many('test_photos', 'imageable')


class OratorTestPhoto(Model):

    __table__ = 'test_photos'
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
