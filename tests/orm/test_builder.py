# -*- coding: utf-8 -*-

from flexmock import flexmock, flexmock_teardown
from .. import OratorTestCase, mock
from ..utils import MockModel, MockQueryBuilder, MockConnection, MockProcessor

from orator.query.grammars.grammar import QueryGrammar
from orator.query.builder import QueryBuilder
from orator.orm.builder import Builder
from orator.orm.model import Model
from orator.exceptions.orm import ModelNotFound
from orator.orm.collection import Collection
from orator.connections import Connection
from orator.query.processors import QueryProcessor


class BuilderTestCase(OratorTestCase):

    def tearDown(self):
        flexmock_teardown()

    def test_find_method(self):
        builder = Builder(self.get_mock_query_builder())
        builder.set_model(self.get_mock_model())
        builder.get_query().where = mock.MagicMock()
        builder.first = mock.MagicMock(return_value='baz')

        result = builder.find('bar', ['column'])

        builder.get_query().where.assert_called_once_with(
            'foo_table.foo', '=', 'bar'
        )
        self.assertEqual('baz', result)

    def test_find_or_new_model_found(self):
        model = self.get_mock_model()
        model.find_or_new = mock.MagicMock(return_value='baz')

        builder = Builder(self.get_mock_query_builder())
        builder.set_model(model)
        builder.get_query().where = mock.MagicMock()
        builder.first = mock.MagicMock(return_value='baz')

        expected = model.find_or_new('bar', ['column'])
        result = builder.find('bar', ['column'])

        builder.get_query().where.assert_called_once_with(
            'foo_table.foo', '=', 'bar'
        )
        self.assertEqual(expected, result)

    def test_find_or_new_model_not_found(self):
        model = self.get_mock_model()
        model.find_or_new = mock.MagicMock(return_value=self.get_mock_model())

        builder = Builder(self.get_mock_query_builder())
        builder.set_model(model)
        builder.get_query().where = mock.MagicMock()
        builder.first = mock.MagicMock(return_value=None)

        result = model.find_or_new('bar', ['column'])
        find_result = builder.find('bar', ['column'])

        builder.get_query().where.assert_called_once_with(
            'foo_table.foo', '=', 'bar'
        )
        self.assertIsNone(find_result)
        self.assertIsInstance(result, Model)

    def test_find_or_fail_raises_model_not_found_exception(self):
        model = self.get_mock_model()

        builder = Builder(self.get_mock_query_builder())
        builder.set_model(model)
        builder.get_query().where = mock.MagicMock()
        builder.first = mock.MagicMock(return_value=None)

        self.assertRaises(
            ModelNotFound,
            builder.find_or_fail,
            'bar',
            ['column']
        )

        builder.get_query().where.assert_called_once_with(
            'foo_table.foo', '=', 'bar'
        )

        builder.first.assert_called_once_with(
            ['column']
        )

    def test_find_or_fail_with_many_raises_model_not_found_exception(self):
        model = self.get_mock_model()

        builder = Builder(self.get_mock_query_builder())
        builder.set_model(model)
        builder.get_query().where_in = mock.MagicMock()
        builder.get = mock.MagicMock(return_value=Collection([1]))

        self.assertRaises(
            ModelNotFound,
            builder.find_or_fail,
            [1, 2],
            ['column']
        )

        builder.get_query().where_in.assert_called_once_with(
            'foo_table.foo', [1, 2]
        )

        builder.get.assert_called_once_with(
            ['column']
        )

    def test_first_or_fail_raises_model_not_found_exception(self):
        model = self.get_mock_model()

        builder = Builder(self.get_mock_query_builder())
        builder.set_model(model)
        builder.first = mock.MagicMock(return_value=None)

        self.assertRaises(
            ModelNotFound,
            builder.first_or_fail,
            ['column']
        )

        builder.first.assert_called_once_with(
            ['column']
        )

    def test_find_with_many(self):
        model = self.get_mock_model()

        builder = Builder(self.get_mock_query_builder())
        builder.set_model(model)
        builder.get_query().where_in = mock.MagicMock()
        builder.get = mock.MagicMock(return_value='baz')

        result = builder.find([1, 2], ['column'])
        self.assertEqual('baz', result)

        builder.get_query().where_in.assert_called_once_with(
            'foo_table.foo', [1, 2]
        )

        builder.get.assert_called_once_with(
            ['column']
        )

    def test_first(self):
        model = self.get_mock_model()

        builder = Builder(self.get_mock_query_builder())
        builder.set_model(model)
        builder.take = mock.MagicMock(return_value=builder)
        builder.get = mock.MagicMock(return_value=Collection(['bar']))

        result = builder.first()
        self.assertEqual('bar', result)

        builder.take.assert_called_once_with(
            1
        )

        builder.get.assert_called_once_with(
            ['*']
        )

    def test_get_loads_models_and_hydrates_eager_relations(self):
        flexmock(Builder)
        builder = Builder(self.get_mock_query_builder())
        builder.should_receive('get_models').with_args(['foo']).and_return(['bar'])
        builder.should_receive('eager_load_relations').with_args(['bar']).and_return(['bar', 'baz'])
        builder.set_model(self.get_mock_model())
        builder.get_model().new_collection = mock.MagicMock(return_value=Collection(['bar', 'baz']))

        results = builder.get(['foo'])
        self.assertEqual(['bar', 'baz'], results.all())

        builder.get_model().new_collection.assert_called_with(['bar', 'baz'])

    def test_get_does_not_eager_relations_when_no_results_are_returned(self):
        flexmock(Builder)
        builder = Builder(self.get_mock_query_builder())
        builder.should_receive('get_models').with_args(['foo']).and_return(['bar'])
        builder.should_receive('eager_load_relations').with_args(['bar']).and_return([])
        builder.set_model(self.get_mock_model())
        builder.get_model().new_collection = mock.MagicMock(return_value=Collection([]))

        results = builder.get(['foo'])
        self.assertEqual([], results.all())

        builder.get_model().new_collection.assert_called_with([])

    def test_pluck_with_model_found(self):
        builder = Builder(self.get_mock_query_builder())

        model = {'name': 'foo'}
        builder.first = mock.MagicMock(return_value=model)

        self.assertEqual('foo', builder.pluck('name'))

        builder.first.assert_called_once_with(
            ['name']
        )

    def test_pluck_with_model_not_found(self):
        builder = Builder(self.get_mock_query_builder())

        builder.first = mock.MagicMock(return_value=None)

        self.assertIsNone(builder.pluck('name'))

    def test_chunk(self):
        builder = Builder(self.get_mock_query_builder())
        results = [['foo1', 'foo2'], ['foo3'], []]
        builder.for_page = mock.MagicMock(return_value=builder)
        builder.get = mock.MagicMock(side_effect=results)

        i = 0
        for result in builder.chunk(2):
            self.assertEqual(result, results[i])

            i += 1

        builder.for_page.assert_has_calls([
            mock.call(1, 2),
            mock.call(2, 2),
            mock.call(3, 2)
        ])

    # TODO: lists with get mutators

    def test_lists_without_model_getters(self):
        builder = self.get_builder()
        builder.get_query().get = mock.MagicMock(return_value=[{'name': 'bar'}, {'name': 'baz'}])
        builder.set_model(self.get_mock_model())
        builder.get_model().has_get_mutator = mock.MagicMock(return_value=False)

        result = builder.lists('name')
        self.assertEqual(['bar', 'baz'], result)

        builder.get_query().get.assert_called_once_with(['name'])

    def test_get_models_hydrates_models(self):
        builder = Builder(self.get_mock_query_builder())
        records = [{
            'name': 'john', 'age': 26
        }, {
            'name': 'jane', 'age': 28
        }]

        builder.get_query().get = mock.MagicMock(return_value=records)
        model = self.get_mock_model()
        builder.set_model(model)
        model.get_connection_name = mock.MagicMock(return_value='foo_connection')
        model.hydrate = mock.MagicMock(return_value=Collection(['hydrated']))
        models = builder.get_models(['foo'])

        self.assertEqual(models, ['hydrated'])

        model.get_table.assert_called_once_with()
        model.get_connection_name.assert_called_once_with()
        model.hydrate.assert_called_once_with(
            records, 'foo_connection'
        )

    def test_macros_are_called_on_builder(self):
        builder = Builder(QueryBuilder(
            flexmock(Connection),
            flexmock(QueryGrammar),
            flexmock(QueryProcessor)
        ))

        def foo_bar(builder):
            builder.foobar = True

            return builder

        builder.macro('foo_bar', foo_bar)
        result = builder.foo_bar()

        self.assertEqual(result, builder)
        self.assertTrue(builder.foobar)

    def test_eager_load_relations_load_top_level_relationships(self):
        flexmock(Builder)
        builder = Builder(flexmock(QueryBuilder(None, None, None)))
        nop1 = lambda: None
        nop2 = lambda: None
        builder.set_eager_loads({'foo': nop1, 'foo.bar': nop2})
        builder.should_receive('_load_relation').with_args(['models'], 'foo', nop1).and_return(['foo'])

        results = builder.eager_load_relations(['models'])
        self.assertEqual(['foo'], results)

    def test_eager_load_accept_queries(self):
        model = OrmBuilderTestModelCloseRelated()
        flexmock(Builder)
        builder = Builder(flexmock(QueryBuilder(None, None, None)))
        nop1 = OrmBuilderTestModelFarRelatedStub.where('id', 5)
        builder.set_eager_loads({'foo': nop1})
        relation = flexmock()
        relation.should_receive('add_eager_constraints').once().with_args(['models'])
        relation.should_receive('init_relation').once().with_args(['models'], 'foo').and_return(['models'])
        relation.should_receive('get_eager').once().and_return(['results'])
        relation.should_receive('match').once()\
            .with_args(['models'], ['results'], 'foo').and_return(['foo'])
        builder.should_receive('get_relation').once().with_args('foo').and_return(relation)
        relation.should_receive('merge_query').with_args(nop1).and_return(relation)

        results = builder.eager_load_relations(['models'])
        self.assertEqual(['foo'], results)

    def test_relationship_eager_load_process(self):
        proof = flexmock()
        flexmock(Builder)
        builder = Builder(flexmock(QueryBuilder(None, None, None)))

        def callback(q):
            proof.foo = q

        builder.set_eager_loads({'orders': callback})
        relation = flexmock()
        relation.should_receive('add_eager_constraints').once().with_args(['models'])
        relation.should_receive('init_relation').once().with_args(['models'], 'orders').and_return(['models'])
        relation.should_receive('get_eager').once().and_return(['results'])
        relation.should_receive('get_query').once().and_return(relation)
        relation.should_receive('match').once()\
            .with_args(['models'], ['results'], 'orders').and_return(['models.matched'])
        builder.should_receive('get_relation').once().with_args('orders').and_return(relation)
        results = builder.eager_load_relations(['models'])

        self.assertEqual(['models.matched'], results)
        self.assertEqual(relation, proof.foo)

    def test_get_relation_properly_sets_nested_relationships(self):
        flexmock(Builder)
        builder = Builder(flexmock(QueryBuilder(None, None, None)))
        model = flexmock(Model())
        relation = flexmock()
        model.set_relation('orders', relation)
        builder.set_model(model)
        relation_query = flexmock()
        relation.should_receive('get_query').and_return(relation_query)
        relation_query.should_receive('with_').once().with_args({'lines': None, 'lines.details': None})
        builder.set_eager_loads({
            'orders': None,
            'orders.lines': None,
            'orders.lines.details': None
        })

        relation = builder.get_relation('orders')

    def test_query_passthru(self):
        builder = self.get_builder()
        builder.get_query().foobar = mock.MagicMock(return_value='foo')

        self.assertIsInstance(builder.foobar(), Builder)
        self.assertEqual(builder.foobar(), builder)

        builder = self.get_builder()
        builder.get_query().insert = mock.MagicMock(return_value='foo')

        self.assertEqual('foo', builder.insert(['bar']))

        builder.get_query().insert.assert_called_once_with(['bar'])

    def test_query_scopes(self):
        builder = self.get_builder()
        builder.get_query().from_ = mock.MagicMock()
        builder.get_query().where = mock.MagicMock()
        model = OrmBuilderTestModelScopeStub()
        builder.set_model(model)
        result = builder.approved()

        self.assertEqual(result, builder)

    def test_simple_where(self):
        builder = self.get_builder()
        builder.get_query().where = mock.MagicMock()
        result = builder.where('foo', '=', 'bar')

        self.assertEqual(builder, result)

        builder.get_query().where.assert_called_once_with('foo', '=', 'bar', 'and')

    def test_nested_where(self):
        nested_query = self.get_builder()
        nested_raw_query = self.get_mock_query_builder()
        nested_query.get_query = mock.MagicMock(return_value=nested_raw_query)
        model = self.get_mock_model()
        builder = self.get_builder()
        builder.set_model(model)
        builder.get_query().add_nested_where_query = mock.MagicMock()

        result = builder.where(nested_query)
        self.assertEqual(builder, result)

        builder.get_query().add_nested_where_query.assert_called_once_with(nested_raw_query, 'and')

    # TODO: nested query with scopes

    def test_delete_override(self):
        builder = self.get_builder()

        builder.on_delete(lambda builder_: {'foo': builder_})

        self.assertEqual({'foo': builder}, builder.delete())

    def test_has_nested(self):
        builder = OrmBuilderTestModelParentStub.where_has('foo', lambda q: q.has('bar'))

        result = OrmBuilderTestModelParentStub.has('foo.bar').to_sql()

        self.assertEqual(builder.to_sql(), result)

    def test_has_nested_with_constraints(self):
        model = OrmBuilderTestModelParentStub

        builder = model.where_has('foo', lambda q: q.where_has('bar', lambda q: q.where('baz', 'bam'))).to_sql()

        result = model.where_has('foo.bar', lambda q: q.where('baz', 'bam')).to_sql()

        self.assertEqual(builder, result)

    def get_builder(self):
        return Builder(self.get_mock_query_builder())

    def get_mock_model(self):
        model = MockModel().prepare_mock()

        return model

    def get_mock_query_builder(self):
        connection = MockConnection().prepare_mock()
        processor = MockProcessor().prepare_mock()

        builder = MockQueryBuilder(
            connection,
            QueryGrammar(),
            processor
        ).prepare_mock()

        return builder


class TestModel(Model):

    @classmethod
    def _boot_columns(cls):
        return []

    @classmethod
    def resolve_connection(cls, connection=None):
        return flexmock(Connection(None))


class OrmBuilderTestModelFarRelatedStub(TestModel):

    pass


class OrmBuilderTestModelScopeStub(TestModel):

    def scope_approved(self, query):
        query.where('foo', 'bar')


class OrmBuilderTestModelCloseRelated(TestModel):

    @property
    def bar(self):
        return self.has_many(OrmBuilderTestModelFarRelatedStub)


class OrmBuilderTestModelParentStub(TestModel):

    @property
    def foo(self):
        return self.belongs_to(OrmBuilderTestModelCloseRelated)
