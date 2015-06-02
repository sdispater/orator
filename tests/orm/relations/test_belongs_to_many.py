# -*- coding: utf-8 -*-


import arrow
from flexmock import flexmock, flexmock_teardown
from ... import OratorTestCase
from ...utils import MockConnection

from orator.query.builder import QueryBuilder
from orator.query.grammars import QueryGrammar
from orator.query.processors import QueryProcessor
from orator.query.expression import QueryExpression
from orator.orm.builder import Builder
from orator.orm.model import Model
from orator.orm.relations import BelongsToMany
from orator.orm.relations.pivot import Pivot
from orator.orm.collection import Collection


class OrmBelongsToTestCase(OratorTestCase):

    def tearDown(self):
        flexmock_teardown()

    def test_models_are_properly_hydrated(self):
        model1 = OrmBelongsToManyModelStub()
        model1.fill(name='john', pivot_user_id=1, pivot_role_id=2)
        model2 = OrmBelongsToManyModelStub()
        model2.fill(name='jane', pivot_user_id=3, pivot_role_id=4)
        models = [model1, model2]

        base_builder = flexmock(Builder(QueryBuilder(MockConnection().prepare_mock(),
                                                     QueryGrammar(), QueryProcessor())))

        relation = self._get_relation()
        relation.get_parent().should_receive('get_connection_name').and_return('foo.connection')
        relation.get_query().get_query().should_receive('add_select').once()\
            .with_args(*['roles.*', 'user_role.user_id AS pivot_user_id', 'user_role.role_id AS pivot_role_id'])\
            .and_return(relation.get_query())
        relation.get_query().should_receive('get_models').once().and_return(models)
        relation.get_query().should_receive('eager_load_relations').once().with_args(models).and_return(models)
        relation.get_related().should_receive('new_collection').replace_with(lambda l: Collection(l))
        relation.get_query().should_receive('get_query').once().and_return(base_builder)

        results = relation.get()

        self.assertIsInstance(results, Collection)

        # Make sure the foreign keys were set on the pivot models
        self.assertEqual('user_id', results[0].pivot.get_foreign_key())
        self.assertEqual('role_id', results[0].pivot.get_other_key())

        self.assertEqual('john', results[0].name)
        self.assertEqual(1, results[0].pivot.user_id)
        self.assertEqual(2, results[0].pivot.role_id)
        self.assertEqual('foo.connection', results[0].pivot.get_connection_name())

        self.assertEqual('jane', results[1].name)
        self.assertEqual(3, results[1].pivot.user_id)
        self.assertEqual(4, results[1].pivot.role_id)
        self.assertEqual('foo.connection', results[1].pivot.get_connection_name())

        self.assertEqual('user_role', results[0].pivot.get_table())
        self.assertTrue(results[0].pivot.exists)

    def test_timestamps_can_be_retrieved_properly(self):
        model1 = OrmBelongsToManyModelStub()
        model1.fill(name='john', pivot_user_id=1, pivot_role_id=2)
        model2 = OrmBelongsToManyModelStub()
        model2.fill(name='jane', pivot_user_id=3, pivot_role_id=4)
        models = [model1, model2]

        base_builder = flexmock(Builder(QueryBuilder(MockConnection().prepare_mock(),
                                                     QueryGrammar(), QueryProcessor())))

        relation = self._get_relation().with_timestamps()
        relation.get_parent().should_receive('get_connection_name').and_return('foo.connection')
        relation.get_query().get_query().should_receive('add_select').once()\
            .with_args(
                'roles.*',
                'user_role.user_id AS pivot_user_id',
                'user_role.role_id AS pivot_role_id',
                'user_role.created_at AS pivot_created_at',
                'user_role.updated_at AS pivot_updated_at'
            )\
            .and_return(relation.get_query())
        relation.get_query().should_receive('get_models').once().and_return(models)
        relation.get_query().should_receive('eager_load_relations').once().with_args(models).and_return(models)
        relation.get_related().should_receive('new_collection').replace_with(lambda l: Collection(l))
        relation.get_query().should_receive('get_query').once().and_return(base_builder)

        results = relation.get()

    def test_models_are_properly_matched_to_parents(self):
        relation = self._get_relation()

        result1 = OrmBelongsToManyModelPivotStub()
        result1.pivot.user_id = 1

        result2 = OrmBelongsToManyModelPivotStub()
        result2.pivot.user_id = 2

        result3 = OrmBelongsToManyModelPivotStub()
        result3.pivot.user_id = 2

        model1 = OrmBelongsToManyModelStub()
        model1.id = 1
        model2 = OrmBelongsToManyModelStub()
        model2.id = 2
        model3 = OrmBelongsToManyModelStub()
        model3.id = 3

        relation.get_related().should_receive('new_collection').replace_with(lambda l=None: Collection(l))
        relation.get_query().should_receive('where').once().with_args('user_role.user_id', '=', 2)
        relation.get_query().should_receive('where').once().with_args('user_role.user_id', '=', 3)
        models = relation.match([model1, model2, model3], Collection([result1, result2, result3]), 'foo')

        self.assertEqual(1, models[0].foo[0].pivot.user_id)
        self.assertEqual(1, len(models[0].foo))
        self.assertEqual(2, models[1].foo[0].pivot.user_id)
        self.assertEqual(2, models[1].foo[1].pivot.user_id)
        self.assertEqual(2, len(models[1].foo))
        self.assertTrue(models[2].foo.is_empty())

    def test_relation_is_properly_initialized(self):
        relation = self._get_relation()
        relation.get_related().should_receive('new_collection').replace_with(lambda l=None: Collection(l or []))
        model = flexmock(Model())
        model.should_receive('set_relation').once().with_args('foo', Collection)
        models = relation.init_relation([model], 'foo')

        self.assertEqual([model], models)

    def test_eager_constraints_are_properly_added(self):
        relation = self._get_relation()
        relation.get_query().get_query().should_receive('where_in').once().with_args('user_role.user_id', [1, 2])
        model1 = OrmBelongsToManyModelStub()
        model1.id = 1
        model2 = OrmBelongsToManyModelStub()
        model2.id = 2

        relation.add_eager_constraints([model1, model2])

    def test_attach_inserts_pivot_table_record(self):
        flexmock(BelongsToMany, touch_if_touching=lambda: True)
        relation = self._get_relation()
        query = flexmock()
        query.should_receive('from_').once().with_args('user_role').and_return(query)
        query.should_receive('insert').once().with_args([{'user_id': 1, 'role_id': 2, 'foo': 'bar'}]).and_return(True)
        mock_query_builder = flexmock()
        relation.get_query().should_receive('get_query').and_return(mock_query_builder)
        mock_query_builder.should_receive('new_query').once().and_return(query)
        relation.should_receive('touch_if_touching').once()

        relation.attach(2, {'foo': 'bar'})

    def test_attach_multiple_inserts_pivot_table_record(self):
        flexmock(BelongsToMany, touch_if_touching=lambda: True)
        relation = self._get_relation()
        query = flexmock()
        query.should_receive('from_').once().with_args('user_role').and_return(query)
        query.should_receive('insert').once().with_args(
            [
                {'user_id': 1, 'role_id': 2, 'foo': 'bar'},
                {'user_id': 1, 'role_id': 3, 'bar': 'baz', 'foo': 'bar'}
            ]
        ).and_return(True)
        mock_query_builder = flexmock()
        relation.get_query().should_receive('get_query').and_return(mock_query_builder)
        mock_query_builder.should_receive('new_query').once().and_return(query)
        relation.should_receive('touch_if_touching').once()

        relation.attach([2, {3: {'bar': 'baz'}}], {'foo': 'bar'})

    def test_attach_inserts_pivot_table_records_with_timestamps_when_ncessary(self):
        flexmock(BelongsToMany, touch_if_touching=lambda: True)
        relation = self._get_relation().with_timestamps()
        query = flexmock()
        query.should_receive('from_').once().with_args('user_role').and_return(query)
        now = arrow.get().naive
        query.should_receive('insert').once().with_args(
            [
                {'user_id': 1, 'role_id': 2, 'foo': 'bar', 'created_at': now, 'updated_at': now}
            ]
        ).and_return(True)
        mock_query_builder = flexmock()
        relation.get_query().should_receive('get_query').and_return(mock_query_builder)
        mock_query_builder.should_receive('new_query').once().and_return(query)
        relation.get_parent().should_receive('fresh_timestamp').once().and_return(now)
        relation.should_receive('touch_if_touching').once()

        relation.attach(2, {'foo': 'bar'})

    def test_attach_inserts_pivot_table_records_with_a_created_at_timestamp(self):
        flexmock(BelongsToMany, touch_if_touching=lambda: True)
        relation = self._get_relation().with_pivot('created_at')
        query = flexmock()
        query.should_receive('from_').once().with_args('user_role').and_return(query)
        now = arrow.get().naive
        query.should_receive('insert').once().with_args(
            [
                {'user_id': 1, 'role_id': 2, 'foo': 'bar', 'created_at': now}
            ]
        ).and_return(True)
        mock_query_builder = flexmock()
        relation.get_query().should_receive('get_query').and_return(mock_query_builder)
        mock_query_builder.should_receive('new_query').once().and_return(query)
        relation.get_parent().should_receive('fresh_timestamp').once().and_return(now)
        relation.should_receive('touch_if_touching').once()

        relation.attach(2, {'foo': 'bar'})

    def test_attach_inserts_pivot_table_records_with_an_updated_at_timestamp(self):
        flexmock(BelongsToMany, touch_if_touching=lambda: True)
        relation = self._get_relation().with_pivot('updated_at')
        query = flexmock()
        query.should_receive('from_').once().with_args('user_role').and_return(query)
        now = arrow.get().naive
        query.should_receive('insert').once().with_args(
            [
                {'user_id': 1, 'role_id': 2, 'foo': 'bar', 'updated_at': now}
            ]
        ).and_return(True)
        mock_query_builder = flexmock()
        relation.get_query().should_receive('get_query').and_return(mock_query_builder)
        mock_query_builder.should_receive('new_query').once().and_return(query)
        relation.get_parent().should_receive('fresh_timestamp').once().and_return(now)
        relation.should_receive('touch_if_touching').once()

        relation.attach(2, {'foo': 'bar'})

    def test_detach_remove_pivot_table_record(self):
        flexmock(BelongsToMany, touch_if_touching=lambda: True)
        relation = self._get_relation()
        query = flexmock()
        query.should_receive('from_').once().with_args('user_role').and_return(query)
        query.should_receive('where').once().with_args('user_id', 1).and_return(query)
        query.should_receive('where_in').once().with_args('role_id', [1, 2, 3])
        query.should_receive('delete').once().and_return(True)
        mock_query_builder = flexmock()
        relation.get_query().should_receive('get_query').and_return(mock_query_builder)
        mock_query_builder.should_receive('new_query').once().and_return(query)
        relation.should_receive('touch_if_touching').once()

        self.assertTrue(relation.detach([1, 2, 3]))

    def test_detach_with_single_id_remove_pivot_table_record(self):
        flexmock(BelongsToMany, touch_if_touching=lambda: True)
        relation = self._get_relation()
        query = flexmock()
        query.should_receive('from_').once().with_args('user_role').and_return(query)
        query.should_receive('where').once().with_args('user_id', 1).and_return(query)
        query.should_receive('where_in').once().with_args('role_id', [1])
        query.should_receive('delete').once().and_return(True)
        mock_query_builder = flexmock()
        relation.get_query().should_receive('get_query').and_return(mock_query_builder)
        mock_query_builder.should_receive('new_query').once().and_return(query)
        relation.should_receive('touch_if_touching').once()

        self.assertTrue(relation.detach(1))

    def test_detach_clears_all_records_when_no_ids(self):
        flexmock(BelongsToMany, touch_if_touching=lambda: True)
        relation = self._get_relation()
        query = flexmock()
        query.should_receive('from_').once().with_args('user_role').and_return(query)
        query.should_receive('where').once().with_args('user_id', 1).and_return(query)
        query.should_receive('where_in').never()
        query.should_receive('delete').once().and_return(True)
        mock_query_builder = flexmock()
        relation.get_query().should_receive('get_query').and_return(mock_query_builder)
        mock_query_builder.should_receive('new_query').once().and_return(query)
        relation.should_receive('touch_if_touching').once()

        self.assertTrue(relation.detach())

    def test_create_creates_new_model_and_insert_attachment_record(self):
        flexmock(BelongsToMany, attach=lambda: True)
        relation = self._get_relation()
        model = flexmock()
        relation.get_related().should_receive('new_instance').once().and_return(model).with_args({'foo': 'bar'})
        model.should_receive('save').once()
        model.should_receive('get_key').and_return('foo')
        relation.should_receive('attach').once().with_args('foo', {'bar': 'baz'}, True)

        self.assertEqual(model, relation.create({'foo': 'bar'}, {'bar': 'baz'}))

    def test_find_or_new_finds_model(self):
        flexmock(BelongsToMany)
        relation = self._get_relation()
        model = flexmock()
        model.foo = 'bar'
        relation.get_query().should_receive('find').with_args('foo', None).and_return(model)
        relation.get_related().should_receive('new_instance').never()

        self.assertEqual('bar', relation.find_or_new('foo').foo)

    def test_find_or_new_returns_new_model(self):
        flexmock(BelongsToMany)
        relation = self._get_relation()
        model = flexmock()
        model.foo = 'bar'
        relation.get_query().should_receive('find').with_args('foo', None).and_return(None)
        relation.get_related().should_receive('new_instance').once().and_return(model)

        self.assertEqual('bar', relation.find_or_new('foo').foo)

    def test_first_or_new_finds_first_model(self):
        flexmock(BelongsToMany)
        relation = self._get_relation()
        model = flexmock()
        model.foo = 'bar'
        relation.get_query().should_receive('where').with_args({'foo': 'bar'}).and_return(relation.get_query())
        relation.get_query().should_receive('first').once().and_return(model)
        relation.get_related().should_receive('new_instance').never()

        self.assertEqual('bar', relation.first_or_new({'foo': 'bar'}).foo)

    def test_first_or_new_returns_new_model(self):
        flexmock(BelongsToMany)
        relation = self._get_relation()
        model = flexmock()
        model.foo = 'bar'
        relation.get_query().should_receive('where').with_args({'foo': 'bar'}).and_return(relation.get_query())
        relation.get_query().should_receive('first').once().and_return(None)
        relation.get_related().should_receive('new_instance').once().and_return(model)

        self.assertEqual('bar', relation.first_or_new({'foo': 'bar'}).foo)

    def test_first_or_create_finds_first_model(self):
        flexmock(BelongsToMany)
        relation = self._get_relation()
        model = flexmock()
        model.foo = 'bar'
        relation.get_query().should_receive('where').with_args({'foo': 'bar'}).and_return(relation.get_query())
        relation.get_query().should_receive('first').once().and_return(model)
        relation.should_receive('create').never()

        self.assertEqual('bar', relation.first_or_create({'foo': 'bar'}).foo)

    def test_first_or_create_returns_new_model(self):
        flexmock(BelongsToMany)
        relation = self._get_relation()
        model = flexmock()
        model.foo = 'bar'
        relation.get_query().should_receive('where').with_args({'foo': 'bar'}).and_return(relation.get_query())
        relation.get_query().should_receive('first').once().and_return(None)
        relation.should_receive('create').once().with_args({'foo': 'bar'}, {}, True).and_return(model)

        self.assertEqual('bar', relation.first_or_create({'foo': 'bar'}).foo)

    def test_update_or_create_finds_first_mode_and_updates(self):
        flexmock(BelongsToMany)
        relation = self._get_relation()
        model = flexmock()
        model.foo = 'bar'
        relation.get_query().should_receive('where').with_args({'foo': 'bar'}).and_return(relation.get_query())
        relation.get_query().should_receive('first').once().and_return(model)
        model.should_receive('fill').once()
        model.should_receive('save').once()
        relation.should_receive('create').never()

        self.assertEqual('bar', relation.update_or_create({'foo': 'bar'}).foo)

    def test_update_or_create_returns_new_model(self):
        flexmock(BelongsToMany)
        relation = self._get_relation()
        model = flexmock()
        model.foo = 'bar'
        relation.get_query().should_receive('where').with_args({'foo': 'bar'}).and_return(relation.get_query())
        relation.get_query().should_receive('first').once().and_return(None)
        relation.should_receive('create').once().with_args({'bar': 'baz'}, None, True).and_return(model)

        self.assertEqual('bar', relation.update_or_create({'foo': 'bar'}, {'bar': 'baz'}).foo)

    def test_sync_syncs_intermediate_table_with_given_list(self):
        for list_ in [[2, 3, 4], ['2', '3', '4']]:
            flexmock(BelongsToMany)
            relation = self._get_relation()
            query = flexmock()
            query.should_receive('from_').once().with_args('user_role').and_return(query)
            query.should_receive('where').once().with_args('user_id', 1).and_return(query)
            mock_query_builder = flexmock()
            relation.get_query().should_receive('get_query').and_return(mock_query_builder)
            mock_query_builder.should_receive('new_query').once().and_return(query)
            query.should_receive('lists').once().with_args('role_id').and_return([1, list_[0], list_[1]])
            relation.should_receive('attach').once().with_args(list_[2], {}, False)
            relation.should_receive('detach').once().with_args([1])
            relation.get_related().should_receive('touches').and_return(False)
            relation.get_parent().should_receive('touches').and_return(False)

            self.assertEqual(
                {
                    'attached': [list_[2]],
                    'detached': [1],
                    'updated': []
                },
                relation.sync(list_)
            )

    def test_sync_syncs_intermediate_table_with_given_list_and_attributes(self):
        flexmock(BelongsToMany)
        relation = self._get_relation()
        query = flexmock()
        query.should_receive('from_').once().with_args('user_role').and_return(query)
        query.should_receive('where').once().with_args('user_id', 1).and_return(query)
        mock_query_builder = flexmock()
        relation.get_query().should_receive('get_query').and_return(mock_query_builder)
        mock_query_builder.should_receive('new_query').once().and_return(query)
        query.should_receive('lists').once().with_args('role_id').and_return([1, 2, 3])
        relation.should_receive('attach').once().with_args(4, {'foo': 'bar'}, False)
        relation.should_receive('update_existing_pivot').once().with_args(3, {'bar': 'baz'}, False).and_return(True)
        relation.should_receive('detach').once().with_args([1])
        relation.should_receive('touch_if_touching').once()
        relation.get_related().should_receive('touches').and_return(False)
        relation.get_parent().should_receive('touches').and_return(False)

        self.assertEqual(
            {
                'attached': [4],
                'detached': [1],
                'updated': [3]
            },
            relation.sync([2, {3: {'bar': 'baz'}}, {4: {'foo': 'bar'}}], )
        )

    def test_sync_does_not_return_values_that_were_not_updated(self):
        flexmock(BelongsToMany)
        relation = self._get_relation()
        query = flexmock()
        query.should_receive('from_').once().with_args('user_role').and_return(query)
        query.should_receive('where').once().with_args('user_id', 1).and_return(query)
        mock_query_builder = flexmock()
        relation.get_query().should_receive('get_query').and_return(mock_query_builder)
        mock_query_builder.should_receive('new_query').once().and_return(query)
        query.should_receive('lists').once().with_args('role_id').and_return([1, 2, 3])
        relation.should_receive('attach').once().with_args(4, {'foo': 'bar'}, False)
        relation.should_receive('update_existing_pivot').once().with_args(3, {'bar': 'baz'}, False).and_return(False)
        relation.should_receive('detach').once().with_args([1])
        relation.should_receive('touch_if_touching').once()
        relation.get_related().should_receive('touches').and_return(False)
        relation.get_parent().should_receive('touches').and_return(False)

        self.assertEqual(
            {
                'attached': [4],
                'detached': [1],
                'updated': []
            },
            relation.sync([2, {3: {'bar': 'baz'}}, {4: {'foo': 'bar'}}], )
        )

    def test_touch_method_syncs_timestamps(self):
        relation = self._get_relation()
        relation.get_related().should_receive('get_updated_at_column').and_return('updated_at')
        now = arrow.get().naive
        relation.get_related().should_receive('fresh_timestamp').and_return(now)
        relation.get_related().should_receive('get_qualified_key_name').and_return('table.id')
        relation.get_query().get_query().should_receive('select').once().with_args('table.id')\
            .and_return(relation.get_query().get_query())
        relation.get_query().should_receive('lists').once().and_return([1, 2, 3])
        query = flexmock()
        relation.get_related().should_receive('new_query').once().and_return(query)
        query.should_receive('where_in').once().with_args('id', [1, 2, 3]).and_return(query)
        query.should_receive('update').once().with_args({'updated_at': now})

        relation.touch()

    def test_touch_if_touching(self):
        flexmock(BelongsToMany)
        relation = self._get_relation()
        relation.should_receive('_touching_parent').once().and_return(True)
        relation.get_parent().should_receive('touch').once()
        relation.get_parent().should_receive('touches').once().with_args('relation_name').and_return(True)
        relation.should_receive('touch').once()

        relation.touch_if_touching()

    def test_sync_method_converts_collection_to_list_of_keys(self):
        flexmock(BelongsToMany)
        relation = self._get_relation()
        query = flexmock()
        query.should_receive('from_').once().with_args('user_role').and_return(query)
        query.should_receive('where').once().with_args('user_id', 1).and_return(query)
        mock_query_builder = flexmock()
        relation.get_query().should_receive('get_query').and_return(mock_query_builder)
        mock_query_builder.should_receive('new_query').once().and_return(query)
        query.should_receive('lists').once().with_args('role_id').and_return([1, 2, 3])

        collection = flexmock(Collection())
        collection.should_receive('model_keys').once().and_return([1, 2, 3])
        relation.should_receive('_format_sync_list').with_args([1, 2, 3]).and_return({1: {}, 2: {}, 3: {}})

        relation.sync(collection)

    def test_where_pivot_params_used_for_new_queries(self):
        flexmock(BelongsToMany)
        relation = self._get_relation()

        relation.get_query().should_receive('where').once().and_return(relation)

        query = flexmock()
        mock_query_builder = flexmock()
        relation.get_query().should_receive('get_query').and_return(mock_query_builder)
        mock_query_builder.should_receive('new_query').once().and_return(query)

        query.should_receive('from_').once().with_args('user_role').and_return(query)

        query.should_receive('where').once().with_args('user_id', 1).and_return(query)

        query.should_receive('where').once().with_args('foo', '=', 'bar', 'and').and_return(query)

        query.should_receive('lists').once().with_args('role_id').and_return([1, 2, 3])
        relation.should_receive('_format_sync_list').with_args([1, 2, 3]).and_return({1: {}, 2: {}, 3: {}})

        relation = relation.where_pivot('foo', '=', 'bar')
        relation.sync([1, 2, 3])

    def _get_relation(self):
        builder, parent = self._get_relation_arguments()[:2]

        return BelongsToMany(builder, parent, 'user_role', 'user_id', 'role_id', 'relation_name')

    def _get_relation_arguments(self):
        flexmock(Model).should_receive('_boot_columns').and_return(['name'])
        parent = flexmock(Model())
        parent.should_receive('get_key').and_return(1)
        parent.should_receive('get_created_at_column').and_return('created_at')
        parent.should_receive('get_updated_at_column').and_return('updated_at')

        query = flexmock(QueryBuilder(MockConnection().prepare_mock(), QueryGrammar(), QueryProcessor()))
        flexmock(Builder)
        builder = Builder(query)
        builder.should_receive('get_query').and_return(query)
        related = flexmock(Model())
        builder.set_model(related)
        builder.should_receive('get_model').and_return(related)

        related.should_receive('new_query').and_return(builder)
        related.should_receive('get_key_name').and_return('id')
        related.should_receive('get_table').and_return('roles')
        related.should_receive('new_pivot').replace_with(lambda *args: Pivot(*args))

        builder.get_query().should_receive('join').at_least().once().with_args('user_role', 'roles.id', '=', 'user_role.role_id')
        builder.should_receive('where').at_least().once().with_args('user_role.user_id', '=', 1)

        return builder, parent, 'user_role', 'user_id', 'role_id', 'relation_id'


class OrmBelongsToManyModelStub(Model):

    __guarded__ = []


class OrmBelongsToManyModelPivotStub(Model):

    __guarded__ = []

    def __init__(self):
        super(OrmBelongsToManyModelPivotStub, self).__init__()

        self.pivot = OrmBelongsToManyPivotStub()


class OrmBelongsToManyPivotStub(object):
    pass
