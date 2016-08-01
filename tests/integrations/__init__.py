# -*- coding: utf-8 -*-

import pendulum
import simplejson as json
from datetime import datetime, timedelta
from orator import Model, Collection, DatabaseManager
from orator.orm import morph_to, has_one, has_many, belongs_to_many, morph_many, belongs_to, scope, accessor
from orator.orm.relations import BelongsToMany
from orator.exceptions.orm import ModelNotFound
from orator.exceptions.query import QueryException


class IntegrationTestCase(object):

    @classmethod
    def setUpClass(cls):
        Model.set_connection_resolver(cls.get_connection_resolver())

    @classmethod
    def get_manager_config(cls):
        raise NotImplementedError()

    @classmethod
    def get_connection_resolver(cls):
        # Adding another connection to test connection switching
        config = cls.get_manager_config()

        config['test'] = {
            'driver': 'sqlite',
            'database': ':memory:'
        }

        return DatabaseManager(config)

    @classmethod
    def tearDownClass(cls):
        Model.unset_connection_resolver()

    @property
    def marker(self):
        return self.grammar().get_marker()

    def setUp(self):
        self.migrate()
        self.migrate('test')

    def tearDown(self):
        self.revert()
        self.revert('test')

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
        self.assertIsInstance(posts[0], OratorTestPost)
        self.assertIsInstance(posts[1], OratorTestPost)
        self.assertIsInstance(post2, OratorTestPost)
        self.assertEqual('Second Post', post2.name)
        self.assertIsInstance(post2.user, OratorTestUser)
        self.assertEqual('john@doe.com', post2.user.email)

    def test_basic_model_hydrate(self):
        OratorTestUser.create(id=1, email='john@doe.com')
        OratorTestUser.create(id=2, email='jane@doe.com')

        models = OratorTestUser.hydrate_raw(
            'SELECT * FROM test_users WHERE email = %s' % self.marker,
            ['jane@doe.com'],
            self.connection().get_name()
        )
        self.assertIsInstance(models, Collection)
        self.assertIsInstance(models[0], OratorTestUser)
        self.assertEqual('jane@doe.com', models[0].email)
        self.assertEqual(self.connection().get_name(), models[0].get_connection_name())
        self.assertEqual(1, len(models))

    def test_has_on_self_referencing_belongs_to_many_relationship(self):
        user = OratorTestUser.create(email='john@doe.com')
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
        user = OratorTestUser.create(email='john@doe.com')
        user.photos().create(name='Avatar 1')
        user.photos().create(name='Avatar 2')
        post = user.posts().create(name='First Post')
        post.photos().create(name='Hero 1')
        post.photos().create(name='Hero 2')

        self.assertIsInstance(user.photos, Collection)
        self.assertIsInstance(user.photos[0], OratorTestPhoto)

        self.assertIsInstance(post.photos, Collection)
        self.assertIsInstance(post.photos[0], OratorTestPhoto)
        self.assertEqual(2, len(user.photos))
        self.assertEqual(2, len(post.photos))
        self.assertEqual('Avatar 1', user.photos[0].name)
        self.assertEqual('Avatar 2', user.photos[1].name)
        self.assertEqual('Hero 1', post.photos[0].name)
        self.assertEqual('Hero 2', post.photos[1].name)

        photos = OratorTestPhoto.order_by('name').get()

        self.assertIsInstance(photos, Collection)
        self.assertEqual(4, len(photos))
        self.assertIsInstance(photos[0].imageable, OratorTestUser)
        self.assertIsInstance(photos[2].imageable, OratorTestPost)
        self.assertEqual('john@doe.com', photos[1].imageable.email)
        self.assertEqual('First Post', photos[3].imageable.name)

    def test_multi_insert_with_different_values(self):
        date = pendulum.utcnow()._datetime
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
        date = pendulum.utcnow()._datetime
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

        self.assertIsInstance(user.friends().with_pivot('id'), BelongsToMany)

    def test_belongs_to_morph_many_eagerload(self):
        user = OratorTestUser.create(id=1, email='john@doe.com')
        user.photos().create(name='Avatar 1')
        user.photos().create(name='Avatar 2')
        post = user.posts().create(name='First Post')
        post.photos().create(name='Hero 1')
        post.photos().create(name='Hero 2')

        posts = OratorTestPost.with_('user', 'photos').get()
        self.assertIsInstance(posts[0].user, OratorTestUser)
        self.assertEqual(user.id, posts[0].user().first().id)
        self.assertIsInstance(posts[0].photos, Collection)
        self.assertEqual(posts[0].photos().where('name', 'Hero 2').first().name, 'Hero 2')

    def test_has_many_eagerload(self):
        user = OratorTestUser.create(id=1, email='john@doe.com')
        post1 = user.posts().create(name='First Post')
        post2 = user.posts().create(name='Second Post')

        user = OratorTestUser.with_('posts').first()
        self.assertIsInstance(user.posts, Collection)
        self.assertEqual(user.posts().where('name', 'Second Post').first().id, post2.id)

    def test_relationships_properties_accept_builder(self):
        user = OratorTestUser.create(id=1, email='john@doe.com')
        post1 = user.posts().create(name='First Post')
        post2 = user.posts().create(name='Second Post')

        user = OratorTestUser.with_('posts').first()
        columns = ', '.join(self.connection().get_query_grammar().wrap_list(['id', 'name', 'user_id']))
        self.assertEqual(
            'SELECT %(columns)s FROM %(table)s WHERE %(table)s.%(user_id)s = %(marker)s ORDER BY %(name)s DESC'
            % {
                'columns': columns,
                'marker': self.marker,
                'table': self.grammar().wrap('test_posts'),
                'user_id': self.grammar().wrap('user_id'),
                'name': self.grammar().wrap('name')
            },
            user.post().to_sql()
        )

        user = OratorTestUser.first()
        self.assertEqual(
            'SELECT %(columns)s FROM %(table)s WHERE %(table)s.%(user_id)s = %(marker)s ORDER BY %(name)s DESC'
            % {
                'columns': columns,
                'marker': self.marker,
                'table': self.grammar().wrap('test_posts'),
                'user_id': self.grammar().wrap('user_id'),
                'name': self.grammar().wrap('name')
            },
            user.post().to_sql()
        )

    def test_morph_to_eagerload(self):
        user = OratorTestUser.create(id=1, email='john@doe.com')
        user.photos().create(name='Avatar 1')
        user.photos().create(name='Avatar 2')
        post = user.posts().create(name='First Post')
        post.photos().create(name='Hero 1')
        post.photos().create(name='Hero 2')

        photo = OratorTestPhoto.with_('imageable').where('name', 'Hero 2').first()
        self.assertIsInstance(photo.imageable, OratorTestPost)
        self.assertEqual(post.id, photo.imageable.id)
        self.assertEqual(post.id, photo.imageable().where('name', 'First Post').first().id)

    def test_json_type(self):
        user = OratorTestUser.create(id=1, email='john@doe.com')
        photo = user.photos().create(name='Avatar 1', metadata={'foo': 'bar'})

        photo = OratorTestPhoto.find(photo.id)
        self.assertEqual('bar', photo.metadata['foo'])

    def test_local_scopes(self):
        yesterday = created_at=datetime.utcnow() - timedelta(days=1)
        john = OratorTestUser.create(id=1, email='john@doe.com', created_at=yesterday, updated_at=yesterday)
        jane = OratorTestUser.create(id=2, email='jane@doe.com')

        result = OratorTestUser.older_than(minutes=30).get()
        self.assertEqual(1, len(result))
        self.assertEqual('john@doe.com', result.first().email)

        result = OratorTestUser.where_not_null('id').older_than(minutes=30).get()
        self.assertEqual(1, len(result))
        self.assertEqual('john@doe.com', result.first().email)

    def test_repr_relations(self):
        user = OratorTestUser.create(id=1, email='john@doe.com')
        photo = user.photos().create(name='Avatar 1', metadata={'foo': 'bar'})

        repr(OratorTestUser.first().photos)
        repr(OratorTestUser.with_('photos').first().photos)

    def test_reconnection(self):
        db = Model.get_connection_resolver()

        db.disconnect()
        db.reconnect()

        db.disconnect()

    def test_raw_query(self):
        user = OratorTestUser.create(id=1, email='john@doe.com')
        photo = user.photos().create(name='Avatar 1', metadata={'foo': 'bar'})

        user = self.connection().table('test_users')\
            .where_raw('test_users.email = %s' % self.get_marker(), 'john@doe.com')\
            .first()

        self.assertEqual(1, user['id'])

        photos = self.connection().select(
            'SELECT * FROM test_photos WHERE imageable_id = %(marker)s and imageable_type = %(marker)s'
            % {"marker": self.get_marker()},
            [str(user['id']), 'test_users']
        )

        self.assertEqual('Avatar 1', photos[0]['name'])

    def test_pivot(self):
        user = OratorTestUser.create(id=1, email='john@doe.com')
        friend = OratorTestUser.create(id=2, email='jane@doe.com')
        another_friend = OratorTestUser.create(id=3, email='another@doe.com')
        user.friends().attach(friend)
        user.friends().attach(another_friend)

        user.friends().update_existing_pivot(friend.id, {'is_close': True})
        self.assertTrue(user.friends().where('test_users.email', 'jane@doe.com').first().pivot.is_close)

    def test_serialization(self):
        user = OratorTestUser.create(id=1, email='john@doe.com')
        photo = user.photos().create(name='Avatar 1', metadata={'foo': 'bar'})

        serialized_user = OratorTestUser.first().serialize()
        serialized_photo = OratorTestPhoto.first().serialize()

        self.assertEqual(1, serialized_user['id'])
        self.assertEqual('john@doe.com', serialized_user['email'])
        self.assertEqual('Avatar 1', serialized_photo['name'])
        self.assertEqual('bar', serialized_photo['metadata']['foo'])
        self.assertEqual('Avatar 1', json.loads(OratorTestPhoto.first().to_json())['name'])

    def test_query_builder_results_attribute_retrieval(self):
        user = OratorTestUser.create(id=1, email='john@doe.com')
        users = self.connection().table('test_users').get()

        self.assertEqual('john@doe.com', users[0].email)
        self.assertEqual('john@doe.com', users[0]['email'])
        self.assertEqual(1, users[0].id)
        self.assertEqual(1, users[0]['id'])

    def test_connection_switching(self):
        OratorTestUser.create(id=1, email='john@doe.com')

        self.assertIsNone(OratorTestUser.on('test').first())
        self.assertIsNotNone(OratorTestUser.first())

        OratorTestUser.on('test').insert(id=1, email='jane@doe.com')
        user = OratorTestUser.on('test').first()
        connection = user.get_connection()
        post = user.posts().create(name='Test')
        self.assertEqual(connection, post.get_connection())

    def grammar(self):
        return self.connection().get_default_query_grammar()

    def connection(self, connection=None):
        return Model.get_connection_resolver().connection(connection)

    def schema(self, connection=None):
        return self.connection(connection).get_schema_builder()

    def migrate(self, connection=None):
        self.schema(connection).drop_if_exists('test_users')
        self.schema(connection).drop_if_exists('test_friends')
        self.schema(connection).drop_if_exists('test_posts')
        self.schema(connection).drop_if_exists('test_photos')

        with self.schema(connection).create('test_users') as table:
            table.increments('id')
            table.string('email').unique()
            table.timestamps(use_current=True)

        with self.schema(connection).create('test_friends') as table:
            table.increments('id')
            table.integer('user_id')
            table.integer('friend_id')
            table.boolean('is_close').default(False)

        with self.schema(connection).create('test_posts') as table:
            table.increments('id')
            table.integer('user_id')
            table.string('name')
            table.timestamps(use_current=True)

        with self.schema(connection).create('test_photos') as table:
            table.increments('id')
            table.morphs('imageable')
            table.string('name')
            table.json('metadata').nullable()
            table.timestamps(use_current=True)

    def revert(self, connection=None):
        self.schema(connection).drop_if_exists('test_users')
        self.schema(connection).drop_if_exists('test_friends')
        self.schema(connection).drop_if_exists('test_posts')
        self.schema(connection).drop_if_exists('test_photos')

    def get_marker(self):
        return '?'


class OratorTestUser(Model):

    __table__ = 'test_users'
    __guarded__ = []

    @belongs_to_many('test_friends', 'user_id', 'friend_id', with_pivot=['id', 'is_close'])
    def friends(self):
        return OratorTestUser

    @has_many('user_id')
    def posts(self):
        return 'test_posts'

    @has_one('user_id')
    def post(self):
        return OratorTestPost.select('id', 'name', 'name', 'user_id').order_by('name', 'desc')

    @morph_many('imageable')
    def photos(self):
        return OratorTestPhoto.order_by('name')

    @scope
    def older_than(self, query, **kwargs):
        query.where('updated_at', '<', (pendulum.utcnow() - timedelta(**kwargs))._datetime)


class OratorTestPost(Model):

    __table__ = 'test_posts'
    __guarded__ = []

    @belongs_to('user_id')
    def user(self):
        return OratorTestUser

    @morph_many('imageable')
    def photos(self):
        return OratorTestPhoto.order_by('name')


class OratorTestPhoto(Model):

    __table__ = 'test_photos'
    __guarded__ = []

    __casts__ = {
        'metadata': 'json'
    }

    @morph_to
    def imageable(self):
        return

    @accessor
    def created_at(self):
        return pendulum.instance(self._attributes['created_at']).to('Europe/Paris')
