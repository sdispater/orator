# -*- coding: utf-8 -*-


import arrow
from flexmock import flexmock, flexmock_teardown
from ... import OratorTestCase, mock

from orator.query.builder import QueryBuilder
from orator.query.grammars import QueryGrammar
from orator.query.expression import QueryExpression
from orator.orm.builder import Builder
from orator.orm.model import Model
from orator.orm.relations import BelongsTo
from orator.orm.collection import Collection


class OrmBelongsToTestCase(OratorTestCase):

    def tearDown(self):
        flexmock_teardown()

    def test_update_retrieve_model_and_updates(self):
        relation = self._get_relation()
        mock = flexmock(Model())
        mock.should_receive('fill').once().with_args({'foo': 'bar'}).and_return(mock)
        mock.should_receive('save').once().and_return(True)
        relation.get_query().should_receive('first').once().and_return(mock)

        self.assertTrue(relation.update({'foo': 'bar'}))

    def test_relation_is_properly_initialized(self):
        relation = self._get_relation()
        model = flexmock(Model())
        model.should_receive('set_relation').once().with_args('foo', None)
        models = relation.init_relation([model], 'foo')

        self.assertEqual([model], models)

    def test_eager_constraints_are_properly_added(self):
        relation = self._get_relation()
        relation.get_query().get_query().should_receive('where_in').once()\
            .with_args('relation.id', ['foreign.value', 'foreign.value.two'])

        model1 = OrmBelongsToModelStub()
        model2 = OrmBelongsToModelStub()
        model2.foreign_key = 'foreign.value'
        model3 = AnotherOrmBelongsToModelStub()
        model3.foreign_key = 'foreign.value.two'
        models = [model1, model2, model3]

        relation.add_eager_constraints(models)

    def test_models_are_properly_matched_to_parents(self):
        relation = self._get_relation()

        result1 = flexmock()
        result1.should_receive('get_attribute').with_args('id').and_return(1)
        result2 = flexmock()
        result2.should_receive('get_attribute').with_args('id').and_return(2)

        model1 = OrmBelongsToModelStub()
        model1.foreign_key = 1
        model2 = OrmBelongsToModelStub()
        model2.foreign_key = 2

        models = relation.match([model1, model2], Collection([result1, result2]), 'foo')

        self.assertEqual(1, models[0].foo.get_attribute('id'))
        self.assertEqual(2, models[1].foo.get_attribute('id'))

    def test_associate_sets_foreign_key_on_model(self):
        parent = Model()
        parent.foreign_key = 'foreign.value'
        parent.get_attribute = mock.MagicMock(return_value='foreign.value')
        parent.set_attribute = mock.MagicMock()
        parent.set_relation = mock.MagicMock()
        relation = self._get_relation(parent)
        associate = flexmock(Model())
        associate.should_receive('get_attribute').once().with_args('id').and_return(1)

        relation.associate(associate)

        parent.get_attribute.assert_has_calls([
            mock.call('foreign_key'),
            mock.call('foreign_key')
        ])
        parent.set_attribute.assert_has_calls([
            mock.call('foreign_key', 1)
        ])
        parent.set_relation.assert_called_once_with('relation', associate)

    def _get_relation(self, parent=None):
        flexmock(Builder)
        query = flexmock(QueryBuilder(None, QueryGrammar(), None))
        builder = Builder(query)
        builder.should_receive('where').with_args('relation.id', '=', 'foreign.value')
        related = flexmock(Model())
        related.should_receive('new_query').and_return(builder)
        related.should_receive('get_key_name').and_return('id')
        related.should_receive('get_table').and_return('relation')
        builder.should_receive('get_model').and_return(related)
        if parent is None:
            parent = OrmBelongsToModelStub()
        parent.foreign_key = 'foreign.value'

        return BelongsTo(builder, parent, 'foreign_key', 'id', 'relation')


class OrmBelongsToModelStub(Model):

    foreign_key = 'foreign.value'


class AnotherOrmBelongsToModelStub(Model):

    foreign_key = 'foreign.value.two'
