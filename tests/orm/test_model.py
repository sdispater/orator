# -*- coding: utf-8 -*-

import simplejson as json
import hashlib
import time
import datetime
from arrow import Arrow
from flexmock import flexmock, flexmock_teardown
from .. import EloquentTestCase, mock
from ..utils import MockModel, MockQueryBuilder, MockConnection, MockProcessor

from eloquent.query.builder import QueryBuilder
from eloquent.query.grammars import QueryGrammar
from eloquent.query.processors import QueryProcessor
from eloquent.orm.builder import Builder
from eloquent.orm.model import Model
from eloquent.exceptions.orm import ModelNotFound, MassAssignmentError
from eloquent.orm.collection import Collection
from eloquent.connections import Connection
from eloquent import DatabaseManager
from eloquent.utils import basestring


class OrmModelTestCase(EloquentTestCase):

    def tearDown(self):
        flexmock_teardown()

    def test_attributes_manipulation(self):
        model = OrmModelStub()
        model.name = 'foo'
        self.assertEqual('foo', model.name)
        del model.name
        self.assertFalse(hasattr(model, 'name'))

        # TODO: mutators

    def test_dirty_attributes(self):
        model = OrmModelStub(foo='1', bar=2, baz=3)
        model.foo = 1
        model.bar = 20
        model.baz = 30

        self.assertTrue(model.is_dirty())
        self.assertTrue(model.is_dirty('foo'))
        self.assertTrue(model.is_dirty('bar'))
        self.assertTrue(model.is_dirty('baz'))
        self.assertTrue(model.is_dirty('foo', 'bar', 'baz'))

    # TODO: test calculated attributes

    def test_new_instance_returns_instance_wit_attributes_set(self):
        model = OrmModelStub()
        instance = model.new_instance({'name': 'john'})
        self.assertIsInstance(instance, OrmModelStub)
        self.assertEqual('john', instance.name)

    def test_hydrate_creates_collection_of_models(self):
        data = [
            {'name': 'john'},
            {'name': 'jane'}
        ]
        collection = OrmModelStub.hydrate(data, 'foo_connection')

        self.assertIsInstance(collection, Collection)
        self.assertEqual(2, len(collection))
        self.assertIsInstance(collection[0], OrmModelStub)
        self.assertIsInstance(collection[1], OrmModelStub)
        self.assertEqual(collection[0].get_attributes(), collection[0].get_original())
        self.assertEqual(collection[1].get_attributes(), collection[1].get_original())
        self.assertEqual('john', collection[0].name)
        self.assertEqual('jane', collection[1].name)
        self.assertEqual('foo_connection', collection[0].get_connection_name())
        self.assertEqual('foo_connection', collection[1].get_connection_name())

    def test_hydrate_raw_makes_raw_query(self):
        model = OrmModelHydrateRawStub()
        connection = MockConnection().prepare_mock()
        connection.select.return_value = []
        model.get_connection = mock.MagicMock(return_value=connection)

        def _set_connection(name):
            model.__connection__ = name

            return model

        OrmModelHydrateRawStub.set_connection = mock.MagicMock(side_effect=_set_connection)
        collection = OrmModelHydrateRawStub.hydrate_raw('SELECT ?', ['foo'])
        self.assertEqual('hydrated', collection)
        connection.select.assert_called_once_with(
            'SELECT ?', ['foo']
        )

    def test_create_saves_new_model(self):
        model = OrmModelSaveStub.create(name='john')
        self.assertTrue(model.get_saved())
        self.assertEqual('john', model.name)

    def test_find_method_calls_query_builder_correctly(self):
        result = OrmModelFindStub.find(1)

        self.assertEqual('foo', result)

    def test_find_use_write_connection(self):
        OrmModelFindWithWriteConnectionStub.on_write_connection().find(1)

    def test_find_with_list_calls_query_builder_correctly(self):
        result = OrmModelFindManyStub.find([1, 2])

        self.assertEqual('foo', result)

    def test_destroy_method_calls_query_builder_correctly(self):
        OrmModelDestroyStub.destroy(1, 2, 3)

    def test_with_calls_query_builder_correctly(self):
        result = OrmModelWithStub.with_('foo', 'bar')
        self.assertEqual('foo', result)

    def test_update_process(self):
        query = flexmock(Builder)
        query.should_receive('where').once().with_args('id', 1)
        query.should_receive('update').once().with_args({'name': 'john'})

        model = OrmModelStub()
        model.new_query = mock.MagicMock(return_value=Builder(QueryBuilder(None, None, None)))
        model._update_timestamps = mock.MagicMock()

        # TODO: events

        model.id = 1
        model.foo = 'bar'
        model.sync_original()
        model.name = 'john'
        model.set_exists(True)
        self.assertTrue(model.save())

        model.new_query.assert_called_once_with()
        model._update_timestamps.assert_called_once_with()

    def test_update_process_does_not_override_timestamps(self):
        query = flexmock(Builder)
        query.should_receive('where').once().with_args('id', 1)
        query.should_receive('update').once().with_args({'created_at': 'foo', 'updated_at': 'bar'})

        model = OrmModelStub()
        model.new_query = mock.MagicMock(return_value=Builder(QueryBuilder(None, None, None)))
        model._update_timestamps = mock.MagicMock()

        # TODO: events

        model.id = 1
        model.sync_original()
        model.created_at = 'foo'
        model.updated_at = 'bar'
        model.set_exists(True)
        self.assertTrue(model.save())

        model.new_query.assert_called_once_with()
        self.assertTrue(model._update_timestamps.called)

    # TODO: update cancelled if updating event return false

    def test_update_process_without_timestamps(self):
        query = flexmock(Builder)
        query.should_receive('where').once().with_args('id', 1)
        query.should_receive('update').once().with_args({'name': 'john'})

        model = OrmModelStub()
        model.__timestamps__ = False
        model.new_query = mock.MagicMock(return_value=Builder(QueryBuilder(None, None, None)))
        model._update_timestamps = mock.MagicMock()

        # TODO: events

        model.id = 1
        model.sync_original()
        model.name = 'john'
        model.set_exists(True)
        self.assertTrue(model.save())

        model.new_query.assert_called_once_with()
        self.assertFalse(model._update_timestamps.called)

    def test_update_process_uses_old_primary_key(self):
        query = flexmock(Builder)
        query.should_receive('where').once().with_args('id', 1)
        query.should_receive('update').once().with_args({'id': 2, 'name': 'john'})

        model = OrmModelStub()
        model.new_query = mock.MagicMock(return_value=Builder(QueryBuilder(None, None, None)))
        model._update_timestamps = mock.MagicMock()

        # TODO: events

        model.id = 1
        model.sync_original()
        model.id = 2
        model.name = 'john'
        model.set_exists(True)
        self.assertTrue(model.save())

        model.new_query.assert_called_once_with()
        self.assertTrue(model._update_timestamps.called)

    def test_timestamps_are_returned_as_objects(self):
        model = Model()
        model.set_raw_attributes({
            'created_at': '2015-03-24',
            'updated_at': '2015-03-24'
        })

        self.assertIsInstance(model.created_at, Arrow)
        self.assertIsInstance(model.updated_at, Arrow)

    def test_timestamps_are_returned_as_objects_from_timestamps_and_datetime(self):
        model = Model()
        model.set_raw_attributes({
            'created_at': datetime.datetime.utcnow(),
            'updated_at': time.time()
        })

        self.assertIsInstance(model.created_at, Arrow)
        self.assertIsInstance(model.updated_at, Arrow)

    def test_timestamps_are_returned_as_objects_on_create(self):
        model = Model()
        model.unguard()

        timestamps = {
            'created_at': datetime.datetime.now(),
            'updated_at': datetime.datetime.now()
        }

        instance = model.new_instance(timestamps)

        self.assertIsInstance(instance.created_at, Arrow)
        self.assertIsInstance(instance.updated_at, Arrow)

        model.reguard()

    def test_timestamps_return_none_if_set_to_none(self):
        model = Model()
        model.unguard()

        timestamps = {
            'created_at': datetime.datetime.now(),
            'updated_at': datetime.datetime.now()
        }

        instance = model.new_instance(timestamps)
        instance.created_at = None

        self.assertIsNone(instance.created_at)

        model.reguard()

    def test_insert_process(self):
        query = flexmock(Builder)

        model = OrmModelStub()
        query_builder = flexmock(QueryBuilder)
        query_builder.should_receive('insert_get_id').once().with_args({'name': 'john'}, 'id').and_return(1)
        model.new_query = mock.MagicMock(return_value=Builder(QueryBuilder(None, None, None)))
        model._update_timestamps = mock.MagicMock()

        # TODO: events

        model.name = 'john'
        model.set_exists(False)
        self.assertTrue(model.save())
        self.assertEqual(1, model.id)
        self.assertTrue(model.exists)
        self.assertTrue(model._update_timestamps.called)

        model = OrmModelStub()
        query_builder.should_receive('insert').once().with_args({'name': 'john'})
        model.new_query = mock.MagicMock(return_value=Builder(QueryBuilder(None, None, None)))
        model._update_timestamps = mock.MagicMock()
        model.set_incrementing(False)

        # TODO: events

        model.name = 'john'
        model.set_exists(False)
        self.assertTrue(model.save())
        self.assertFalse(hasattr(model, 'id'))
        self.assertTrue(model.exists)
        self.assertTrue(model._update_timestamps.called)

    # TODO: insert cancelled if creating event return false

    def test_delete_properly_deletes_model(self):
        query = flexmock(Builder)
        model = OrmModelStub()
        builder = Builder(QueryBuilder(None, None, None))
        query.should_receive('where').once().with_args('id', 1).and_return(builder)
        query.should_receive('delete').once()
        model.new_query = mock.MagicMock(return_value=builder)
        model._touch_owners = mock.MagicMock()

        model.set_exists(True)
        model.id = 1
        model.delete()

        self.assertTrue(model._touch_owners.called)

    def test_push_no_relations(self):
        flexmock(Builder)
        model = flexmock(Model())
        query = flexmock(QueryBuilder(MockConnection().prepare_mock(), QueryGrammar(), QueryProcessor()))
        builder = Builder(query)
        builder.get_query().should_receive('insert_get_id').once().with_args({'name': 'john'}, 'id').and_return(1)
        model.should_receive('new_query').once().and_return(builder)
        model.should_receive('_update_timestamps').once()

        model.name = 'john'
        model.set_exists(False)

        self.assertTrue(model.push())
        self.assertEqual(1, model.id)
        self.assertTrue(model.exists)

    def test_push_empty_one_relation(self):
        flexmock(Builder)
        model = flexmock(Model())
        query = flexmock(QueryBuilder(MockConnection().prepare_mock(), QueryGrammar(), QueryProcessor()))
        builder = Builder(query)
        builder.get_query().should_receive('insert_get_id').once().with_args({'name': 'john'}, 'id').and_return(1)
        model.should_receive('new_query').once().and_return(builder)
        model.should_receive('_update_timestamps').once()

        model.name = 'john'
        model.set_exists(False)
        model.set_relation('relation_one', None)

        self.assertTrue(model.push())
        self.assertEqual(1, model.id)
        self.assertTrue(model.exists)
        self.assertIsNone(model.relation_one)

    def test_push_one_relation(self):
        flexmock(Builder)
        related1 = flexmock(Model())
        query = flexmock(QueryBuilder(MockConnection().prepare_mock(), QueryGrammar(), QueryProcessor()))
        builder = Builder(query)
        builder.get_query().should_receive('insert_get_id').once().with_args({'name': 'related1'}, 'id').and_return(2)
        related1.should_receive('new_query').once().and_return(builder)
        related1.should_receive('_update_timestamps').once()

        related1.name = 'related1'
        related1.set_exists(False)

        model = flexmock(Model())
        model.should_receive('resolve_connection').and_return(MockConnection().prepare_mock())
        query = flexmock(QueryBuilder(MockConnection().prepare_mock(), QueryGrammar(), QueryProcessor()))
        builder = Builder(query)
        builder.get_query().should_receive('insert_get_id').once().with_args({'name': 'john'}, 'id').and_return(1)
        model.should_receive('new_query').once().and_return(builder)
        model.should_receive('_update_timestamps').once()

        model.name = 'john'
        model.set_exists(False)
        model.set_relation('relation_one', related1)

        self.assertTrue(model.push())
        self.assertEqual(1, model.id)
        self.assertTrue(model.exists)
        self.assertEqual(2, model.relation_one.id)
        self.assertTrue(model.relation_one.exists)
        self.assertEqual(2, related1.id)
        self.assertTrue(related1.exists)

    def test_push_empty_many_relation(self):
        flexmock(Builder)
        model = flexmock(Model())
        query = flexmock(QueryBuilder(MockConnection().prepare_mock(), QueryGrammar(), QueryProcessor()))
        builder = Builder(query)
        builder.get_query().should_receive('insert_get_id').once().with_args({'name': 'john'}, 'id').and_return(1)
        model.should_receive('new_query').once().and_return(builder)
        model.should_receive('_update_timestamps').once()

        model.name = 'john'
        model.set_exists(False)
        model.set_relation('relation_many', Collection([]))

        self.assertTrue(model.push())
        self.assertEqual(1, model.id)
        self.assertTrue(model.exists)
        self.assertEqual(0, len(model.relation_many))

    def test_push_many_relation(self):
        flexmock(Builder)
        related1 = flexmock(Model())
        query = flexmock(QueryBuilder(MockConnection().prepare_mock(), QueryGrammar(), QueryProcessor()))
        builder = Builder(query)
        builder.get_query().should_receive('insert_get_id').once().with_args({'name': 'related1'}, 'id').and_return(2)
        related1.should_receive('new_query').once().and_return(builder)
        related1.should_receive('_update_timestamps').once()

        related1.name = 'related1'
        related1.set_exists(False)

        flexmock(Builder)
        related2 = flexmock(Model())
        query = flexmock(QueryBuilder(MockConnection().prepare_mock(), QueryGrammar(), QueryProcessor()))
        builder = Builder(query)
        builder.get_query().should_receive('insert_get_id').once().with_args({'name': 'related2'}, 'id').and_return(3)
        related2.should_receive('new_query').once().and_return(builder)
        related2.should_receive('_update_timestamps').once()

        related2.name = 'related2'
        related2.set_exists(False)

        model = flexmock(Model())
        model.should_receive('resolve_connection').and_return(MockConnection().prepare_mock())
        query = flexmock(QueryBuilder(MockConnection().prepare_mock(), QueryGrammar(), QueryProcessor()))
        builder = Builder(query)
        builder.get_query().should_receive('insert_get_id').once().with_args({'name': 'john'}, 'id').and_return(1)
        model.should_receive('new_query').once().and_return(builder)
        model.should_receive('_update_timestamps').once()

        model.name = 'john'
        model.set_exists(False)
        model.set_relation('relation_many', Collection([related1, related2]))

        self.assertTrue(model.push())
        self.assertEqual(1, model.id)
        self.assertTrue(model.exists)
        self.assertEqual(2, len(model.relation_many))
        self.assertEqual([2, 3], model.relation_many.lists('id'))

    def test_new_query_returns_eloquent_query_builder(self):
        conn = flexmock(Connection)
        grammar = flexmock(QueryGrammar)
        processor = flexmock(QueryProcessor)
        conn.should_receive('get_query_grammar').and_return(grammar)
        conn.should_receive('get_post_processor').and_return(processor)
        resolver = flexmock(DatabaseManager)
        resolver.should_receive('connection').and_return(Connection(None))
        OrmModelStub.set_connection_resolver(DatabaseManager({}))

        model = OrmModelStub()
        builder = model.new_query()
        self.assertIsInstance(builder, Builder)

    def test_get_and_set_table(self):
        model = OrmModelStub()
        self.assertEqual('stub', model.get_table())
        model.set_table('foo')
        self.assertEqual('foo', model.get_table())

    def test_get_key_returns_primary_key_value(self):
        model = OrmModelStub()
        model.id = 1
        self.assertEqual(1, model.get_key())
        self.assertEqual('id', model.get_key_name())

    def test_connection_management(self):
        resolver = flexmock(DatabaseManager)
        resolver.should_receive('connection').once().with_args('foo').and_return('bar')

        OrmModelStub.set_connection_resolver(DatabaseManager({}))
        model = OrmModelStub()
        model.set_connection('foo')

        self.assertEqual('bar', model.get_connection())

    def test_to_dict(self):
        model = OrmModelStub()
        model.name = 'foo'
        model.age = None
        model.password = 'password1'
        model.set_hidden(['password'])

        # TODO: relations

        d = model.to_dict()

        self.assertIsInstance(d, dict)
        self.assertEqual('foo', d['name'])
        self.assertIsNone(d['age'])

        # TODO: relations

    def test_to_dict_includes_default_formatted_timestamps(self):
        model = Model()
        model.set_raw_attributes({
            'created_at': '2015-03-24',
            'updated_at': '2015-03-25'
        })

        d = model.to_dict()

        self.assertEqual('2015-03-24T00:00:00+00:00', d['created_at'])
        self.assertEqual('2015-03-25T00:00:00+00:00', d['updated_at'])

    def test_to_dict_includes_custom_formatted_timestamps(self):
        class Stub(Model):

            def get_date_format(self):
                return 'DD-MM-YY'

        model = Stub()
        model.set_raw_attributes({
            'created_at': '2015-03-24',
            'updated_at': '2015-03-25'
        })

        d = model.to_dict()

        self.assertEqual('24-03-15', d['created_at'])
        self.assertEqual('25-03-15', d['updated_at'])

    def test_visible_creates_dict_whitelist(self):
        model = OrmModelStub()
        model.set_visible(['name'])
        model.name = 'John'
        model.age = 28
        d = model.to_dict()

        self.assertEqual({'name': 'John'}, d)

    # TODO: hidden also hides relationship

    # TODO: to_dict uses mutators

    def test_hidden_are_ignored_when_visible(self):
        model = OrmModelStub(name='john', age=28, id='foo')
        model.set_visible(['name', 'id'])
        model.set_hidden(['name', 'age'])
        d = model.to_dict()

        self.assertIn('name', d)
        self.assertIn('id', d)
        self.assertNotIn('age', d)

    def test_fillable(self):
        model = OrmModelStub()
        model.fillable(['name', 'age'])
        model.fill(name='foo', age=28)
        self.assertEqual('foo', model.name)
        self.assertEqual(28, model.age)

    def test_unguard_allows_anything(self):
        model = OrmModelStub()
        model.unguard()
        model.guard(['*'])
        model.fill(name='foo', age=28)
        self.assertEqual('foo', model.name)
        self.assertEqual(28, model.age)
        model.reguard()

    def test_underscore_properties_are_not_filled(self):
        model = OrmModelStub()
        model.fill(_foo='bar')
        self.assertEqual({}, model.get_attributes())

    def test_guarded(self):
        model = OrmModelStub()
        model.guard(['name', 'age'])
        model.fill(name='foo', age='bar', foo='bar')
        self.assertFalse(hasattr(model, 'name'))
        self.assertFalse(hasattr(model, 'age'))
        self.assertEqual('bar', model.foo)

    def test_fillable_overrides_guarded(self):
        model = OrmModelStub()
        model.guard(['name', 'age'])
        model.fillable(['age', 'foo'])
        model.fill(name='foo', age='bar', foo='bar')
        self.assertFalse(hasattr(model, 'name'))
        self.assertEqual('bar', model.age)
        self.assertEqual('bar', model.foo)

    def test_global_guarded(self):
        model = OrmModelStub()
        model.guard(['*'])
        self.assertRaises(
            MassAssignmentError,
            model.fill,
            name='foo', age='bar', foo='bar'
        )

    # TODO: test relations

    def test_models_assumes_their_name(self):
        model = OrmModelNoTableStub()

        self.assertEqual('orm_model_no_table_stubs', model.get_table())

    # TODO: mutators cache

    def test_clone_model_makes_a_fresh_copy(self):
        model = OrmModelStub()
        model.id = 1
        model.set_exists(True)
        model.first = 'john'
        model.last = 'doe'
        model.created_at = model.fresh_timestamp()
        model.updated_at = model.fresh_timestamp()
        # TODO: relation

        clone = model.replicate()

        self.assertFalse(hasattr(clone, 'id'))
        self.assertFalse(clone.exists)
        self.assertEqual('john', clone.first)
        self.assertEqual('doe', clone.last)
        self.assertFalse(hasattr(clone, 'created_at'))
        self.assertFalse(hasattr(clone, 'updated_at'))
        # TODO: relation

        clone.first = 'jane'

        self.assertEqual('john', model.first)
        self.assertEqual('jane', clone.first)

    def test_get_attribute_raise_attribute_error(self):
        model = OrmModelStub()

        try:
            relation = model.incorrect_relation
            self.fail('AttributeError not raised')
        except AttributeError:
            pass

    def test_increment(self):
        query = flexmock()
        model_mock = flexmock(OrmModelStub, new_query=lambda: query)
        model = OrmModelStub()
        model.set_exists(True)
        model.id = 1
        model.sync_original_attribute('id')
        model.foo = 2

        model_mock.should_receive('new_query').and_return(query)
        query.should_receive('where').and_return(query)
        query.should_receive('increment')

        model.public_increment('foo')

        self.assertEqual(3, model.foo)
        self.assertFalse(model.is_dirty())

    # TODO: relationship touch_owners is propagated

    # TODO: relationship touch_owners is not propagated if no relationship result

    def test_timestamps_are_not_update_with_timestamps_false_save_option(self):
        query = flexmock(Builder)
        query.should_receive('where').once().with_args('id', 1)
        query.should_receive('update').once().with_args({'name': 'john'})

        model = OrmModelStub()
        model.new_query = mock.MagicMock(return_value=Builder(QueryBuilder(None, None, None)))

        model.id = 1
        model.sync_original()
        model.name = 'john'
        model.set_exists(True)
        self.assertTrue(model.save({'timestamps': False}))
        self.assertFalse(hasattr(model, 'updated_at'))

        model.new_query.assert_called_once_with()

    def test_casts(self):
        model = OrmModelCastingStub()
        model.first = '3'
        model.second = '4.0'
        model.third = 2.5
        model.fourth = 1
        model.fifth = 0
        model.sixth = {'foo': 'bar'}
        model.seventh = ['foo', 'bar']
        model.eighth = {'foo': 'bar'}

        self.assertIsInstance(model.first, int)
        self.assertIsInstance(model.second, float)
        self.assertIsInstance(model.third, basestring)
        self.assertIsInstance(model.fourth, bool)
        self.assertIsInstance(model.fifth, bool)
        self.assertIsInstance(model.sixth, dict)
        self.assertIsInstance(model.seventh, list)
        self.assertIsInstance(model.eighth, dict)
        self.assertTrue(model.fourth)
        self.assertFalse(model.fifth)
        self.assertEqual({'foo': 'bar'}, model.sixth)
        self.assertEqual({'foo': 'bar'}, model.eighth)
        self.assertEqual(['foo', 'bar'], model.seventh)
        
        d = model.to_dict()
        
        self.assertIsInstance(d['first'], int)
        self.assertIsInstance(d['second'], float)
        self.assertIsInstance(d['third'], basestring)
        self.assertIsInstance(d['fourth'], bool)
        self.assertIsInstance(d['fifth'], bool)
        self.assertIsInstance(d['sixth'], dict)
        self.assertIsInstance(d['seventh'], list)
        self.assertIsInstance(d['eighth'], dict)
        self.assertTrue(d['fourth'])
        self.assertFalse(d['fifth'])
        self.assertEqual({'foo': 'bar'}, d['sixth'])
        self.assertEqual({'foo': 'bar'}, d['eighth'])
        self.assertEqual(['foo', 'bar'], d['seventh'])

    def test_casts_preserve_null(self):
        model = OrmModelCastingStub()
        model.first = None
        model.second = None
        model.third = None
        model.fourth = None
        model.fifth = None
        model.sixth = None
        model.seventh = None
        model.eighth = None

        self.assertIsNone(model.first)
        self.assertIsNone(model.second)
        self.assertIsNone(model.third)
        self.assertIsNone(model.fourth)
        self.assertIsNone(model.fifth)
        self.assertIsNone(model.sixth)
        self.assertIsNone(model.seventh)
        self.assertIsNone(model.eighth)
        
        d = model.to_dict()
        
        self.assertIsNone(d['first'])
        self.assertIsNone(d['second'])
        self.assertIsNone(d['third'])
        self.assertIsNone(d['fourth'])
        self.assertIsNone(d['fifth'])
        self.assertIsNone(d['sixth'])
        self.assertIsNone(d['seventh'])
        self.assertIsNone(d['eighth'])


class OrmModelStub(Model):

    __table__ = 'stub'

    __guarded__ = []

    def get_list_items_attribute(self, value):
        return json.loads(value)

    def set_list_items_attribute(self, value):
        self._attributes['list_items'] = json.dumps(value)

    def get_password_attribute(self, _):
        return '******'

    def set_password_attribute(self, value):
        self._attributes['password_hash'] = hashlib.md5(value).hexdigest()

    def public_increment(self, column, amount=1):
        return self._increment(column, amount)

    def get_dates(self):
        return []


class OrmModelHydrateRawStub(Model):

    @classmethod
    def hydrate(cls, items, connection=None):
        return 'hydrated'


class OrmModelWithStub(Model):

    def new_query(self):
        mock = flexmock(Builder(None))
        mock.should_receive('with_').once().with_args('foo', 'bar').and_return('foo')

        return mock


class OrmModelSaveStub(Model):

    __table__ = 'save_stub'

    __guarded__ = []

    __saved = False

    def save(self, options=None):
        self.__saved = True

    def set_incrementing(self, value):
        self.__incrementing__ = value

    def get_saved(self):
        return self.__saved


class OrmModelFindStub(Model):

    def new_query(self):
        flexmock(Builder).should_receive('find').once().with_args(1, ['*']).and_return('foo')

        return Builder(None)


class OrmModelFindWithWriteConnectionStub(Model):

    def new_query(self):
        mock = flexmock(Builder)
        mock_query = flexmock(QueryBuilder)
        mock_query.should_receive('use_write_connection').once().and_return(flexmock)
        mock.should_receive('find').once().with_args(1).and_return('foo')

        return Builder(QueryBuilder(None, None, None))


class OrmModelFindManyStub(Model):

    def new_query(self):
        mock = flexmock(Builder)
        mock.should_receive('find').once().with_args([1, 2], ['*']).and_return('foo')

        return Builder(QueryBuilder(None, None, None))


class OrmModelDestroyStub(Model):

    def new_query(self):
        mock = flexmock(Builder)
        model = flexmock()
        mock_query = flexmock(QueryBuilder)
        mock_query.should_receive('where_in').once().with_args('id', [1, 2, 3]).and_return(flexmock)
        mock.should_receive('get').once().and_return([model])
        model.should_receive('delete').once()

        return Builder(QueryBuilder(None, None, None))


class OrmModelNoTableStub(Model):

    pass


class OrmModelCastingStub(Model):

    __casts__ = {
        'first': 'int',
        'second': 'float',
        'third': 'str',
        'fourth': 'bool',
        'fifth': 'boolean',
        'sixth': 'dict',
        'seventh': 'list',
        'eighth': 'json'
    }
