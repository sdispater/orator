# -*- coding: utf-8 -*-

import arrow
from flexmock import flexmock, flexmock_teardown
from ... import OratorTestCase

from orator.query.builder import QueryBuilder
from orator.query.grammars import QueryGrammar
from orator.query.expression import QueryExpression
from orator.orm.builder import Builder
from orator.orm.model import Model
from orator.orm.relations import MorphTo
from orator.orm.collection import Collection


class OrmMorphToTestCase(OratorTestCase):

    def tearDown(self):
        flexmock_teardown()

    def test_lookup_dictionary_is_properly_constructed(self):
        relation = self._get_relation()

        one = flexmock()
        one.morph_type = 'morph_type_1'
        one.foreign_key = 'foreign_key_1'
        two = flexmock()
        two.morph_type = 'morph_type_1'
        two.foreign_key = 'foreign_key_1'
        three = flexmock()
        three.morph_type = 'morph_type_2'
        three.foreign_key = 'foreign_key_2'

        relation.add_eager_constraints([one, two, three])

        dictionary = relation.get_dictionary()

        self.assertEqual({
            'morph_type_1': {
                'foreign_key_1': [
                    one,
                    two
                ]
            },
            'morph_type_2': {
                'foreign_key_2': [three]
            }
        }, dictionary)

    def test_models_are_properly_pulled_and_matched(self):
        relation = self._get_relation()

        one = flexmock(Model())
        one.morph_type = 'morph_type_1'
        one.foreign_key = 'foreign_key_1'
        two = flexmock(Model())
        two.morph_type = 'morph_type_1'
        two.foreign_key = 'foreign_key_1'
        three = flexmock(Model())
        three.morph_type = 'morph_type_2'
        three.foreign_key = 'foreign_key_2'

        relation.add_eager_constraints([one, two, three])

        first_query = flexmock(Builder(flexmock(QueryBuilder(None, QueryGrammar(), None))))
        second_query = flexmock(Builder(flexmock(QueryBuilder(None, QueryGrammar(), None))))
        first_model = flexmock(Model())
        second_model = flexmock(Model())
        relation.should_receive('_create_model_by_type').once().with_args('morph_type_1').and_return(first_model)
        relation.should_receive('_create_model_by_type').once().with_args('morph_type_2').and_return(second_model)
        first_model.should_receive('get_key_name').and_return('id')
        second_model.should_receive('get_key_name').and_return('id')

        first_model.should_receive('new_query').once().and_return(first_query)
        second_model.should_receive('new_query').once().and_return(second_query)

        first_query.get_query().should_receive('where_in').once()\
            .with_args('id', ['foreign_key_1']).and_return(first_query)
        result_one = flexmock()
        first_query.should_receive('get').and_return(Collection.make([result_one]))
        result_one.should_receive('get_key').and_return('foreign_key_1')

        second_query.get_query().should_receive('where_in').once()\
            .with_args('id', ['foreign_key_2']).and_return(second_query)
        result_two = flexmock()
        second_query.should_receive('get').and_return(Collection.make([result_two]))
        result_two.should_receive('get_key').and_return('foreign_key_2')

        one.should_receive('set_relation').once().with_args('relation', result_one)
        two.should_receive('set_relation').once().with_args('relation', result_one)
        three.should_receive('set_relation').once().with_args('relation', result_two)

        relation.get_eager()

    # TODO: soft deletes

    def test_associate_sets_foreign_key_and_type_on_model(self):
        parent = flexmock(Model())
        parent.should_receive('get_attribute').once().with_args('foreign_key').and_return('foreign.value')

        relation = self._get_relation_associate(parent)

        associate = flexmock(Model())
        associate.should_receive('get_key').once().and_return(1)
        associate.should_receive('get_morph_class').once().and_return('Model')

        parent.should_receive('set_attribute').once().with_args('foreign_key', 1)
        parent.should_receive('set_attribute').once().with_args('morph_type', 'Model')
        parent.should_receive('set_relation').once().with_args('relation', associate)

        relation.associate(associate)

    def _get_relation_associate(self, parent):
        flexmock(Builder)
        query = flexmock(QueryBuilder(None, QueryGrammar(), None))
        builder = Builder(query)
        builder.should_receive('where').with_args('relation.id', '=', 'foreign.value')
        related = flexmock(Model())
        related.should_receive('get_key').and_return(1)
        related.should_receive('get_table').and_return('relation')
        builder.should_receive('get_model').and_return(related)

        return MorphTo(builder, parent, 'foreign_key', 'id', 'morph_type', 'relation')

    def _get_relation(self, parent=None, builder=None):
        flexmock(Builder)
        query = flexmock(QueryBuilder(None, QueryGrammar(), None))
        builder = builder or Builder(query)
        builder.should_receive('where').with_args('relation.id', '=', 'foreign.value')
        related = flexmock(Model())
        related.should_receive('get_key').and_return(1)
        related.should_receive('get_table').and_return('relation')
        builder.should_receive('get_model').and_return(related)

        parent = parent or OrmMorphToModelStub()

        flexmock(MorphTo)
        return MorphTo(builder, parent, 'foreign_key', 'id', 'morph_type', 'relation')


class OrmMorphToModelStub(Model):

    foreign_key = 'foreign.value'
