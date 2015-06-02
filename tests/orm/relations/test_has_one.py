# -*- coding: utf-8 -*-


import arrow
from flexmock import flexmock, flexmock_teardown
from ... import OratorTestCase

from orator.query.builder import QueryBuilder
from orator.query.grammars import QueryGrammar
from orator.query.expression import QueryExpression
from orator.orm.builder import Builder
from orator.orm.model import Model
from orator.orm.relations import HasOne
from orator.orm.collection import Collection


class OrmHasOneTestCase(OratorTestCase):

    def tearDown(self):
        flexmock_teardown()

    def test_save_method_set_foreign_key_on_model(self):
        relation = self._get_relation()
        mock_model = flexmock(Model(), save=lambda: True)
        mock_model.should_receive('save').once().and_return(True)
        result = relation.save(mock_model)

        attributes = result.get_attributes()
        self.assertEqual(1, attributes['foreign_key'])

    def test_create_properly_creates_new_model(self):
        relation = self._get_relation()
        created = flexmock(Model(), save=lambda: True, set_attribute=lambda: None)
        created.should_receive('save').once().and_return(True)
        relation.get_related().should_receive('new_instance').once().with_args({'name': 'john'}).and_return(created)
        created.should_receive('set_attribute').with_args('foreign_key', 1)

        self.assertEqual(created, relation.create(name='john'))

    def test_update_updates_models_with_timestamps(self):
        relation = self._get_relation()
        relation.get_related().should_receive('uses_timestamps').once().and_return(True)
        now = arrow.get()
        relation.get_related().should_receive('fresh_timestamp').once().and_return(now)
        relation.get_query().should_receive('update').once().with_args({'foo': 'bar', 'updated_at': now}).and_return('results')

        self.assertEqual('results', relation.update(foo='bar'))

    def test_relation_is_properly_initialized(self):
        relation = self._get_relation()
        model = flexmock(Model())
        model.should_receive('set_relation').once().with_args('foo', None)
        models = relation.init_relation([model], 'foo')

        self.assertEqual([model], models)

    def test_eager_constraints_are_properly_added(self):
        relation = self._get_relation()
        relation.get_query().get_query().should_receive('where_in').once().with_args('table.foreign_key', [1, 2])

        model1 = OrmHasOneModelStub()
        model1.id = 1
        model2 = OrmHasOneModelStub()
        model2.id = 2

        relation.add_eager_constraints([model1, model2])

    def test_models_are_properly_matched_to_parents(self):
        relation = self._get_relation()

        result1 = OrmHasOneModelStub()
        result1.foreign_key = 1
        result2 = OrmHasOneModelStub()
        result2.foreign_key = 2

        model1 = OrmHasOneModelStub()
        model1.id = 1
        model2 = OrmHasOneModelStub()
        model2.id = 2
        model3 = OrmHasOneModelStub()
        model3.id = 3

        relation.get_query().should_receive('where').with_args('table.foreign_key', '=', 2)
        relation.get_query().should_receive('where').with_args('table.foreign_key', '=', 3)

        models = relation.match([model1, model2, model3], Collection([result1, result2]), 'foo')

        self.assertEqual(1, models[0].foo.foreign_key)
        self.assertEqual(2, models[1].foo.foreign_key)
        self.assertEqual(None, models[2].foo)

    def test_relation_count_query_can_be_built(self):
        relation = self._get_relation()
        query = flexmock(QueryBuilder(None, QueryGrammar(), None))
        builder = Builder(query)
        builder.get_query().should_receive('select').once()
        relation.get_parent().should_receive('get_table').and_return('table')
        builder.should_receive('where').once().with_args('table.foreign_key', '=', QueryExpression)
        parent_query = flexmock(QueryBuilder(None, None, None))
        relation.get_query().should_receive('get_query').and_return(parent_query)
        grammar = flexmock()
        parent_query.should_receive('get_grammar').once().and_return(grammar)
        grammar.should_receive('wrap').once().with_args('table.id')

        relation.get_relation_count_query(builder, builder)

    def _get_relation(self):
        flexmock(Builder)
        query = flexmock(QueryBuilder(None, QueryGrammar(), None))
        builder = Builder(query)
        builder.should_receive('where').with_args('table.foreign_key', '=', 1)
        related = flexmock(Model())
        related_query = QueryBuilder(None, QueryGrammar(), None)
        related.should_receive('new_query').and_return(Builder(related_query))
        builder.should_receive('get_model').and_return(related)
        parent = flexmock(Model())
        parent.should_receive('get_attribute').with_args('id').and_return(1)
        parent.should_receive('get_created_at_column').and_return('created_at')
        parent.should_receive('get_updated_at_column').and_return('updated_at')
        parent.should_receive('new_query').and_return(builder)

        return HasOne(builder, parent, 'table.foreign_key', 'id')


class OrmHasOneModelStub(Model):

    pass
