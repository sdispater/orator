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
from orator.orm.relations import MorphToMany
from orator.orm.relations.pivot import Pivot
from orator.orm.collection import Collection


class OrmMorphToManyTestCase(OratorTestCase):

    def tearDown(self):
        flexmock_teardown()

    def test_eager_constraints_are_properly_added(self):
        relation = self._get_relation()
        relation.get_query().get_query().should_receive('where_in').once().with_args('taggables.taggable_id', [1, 2])
        relation.get_query().should_receive('where').once()\
            .with_args('taggables.taggable_type', relation.get_parent().__class__.__name__)
        model1 = OrmMorphToManyModelStub()
        model1.id = 1
        model2 = OrmMorphToManyModelStub()
        model2.id = 2

        relation.add_eager_constraints([model1, model2])

    def test_attach_inserts_pivot_table_record(self):
        flexmock(MorphToMany, touch_if_touching=lambda: True)
        relation = self._get_relation()
        query = flexmock()
        query.should_receive('from_').once().with_args('taggables').and_return(query)
        query.should_receive('insert').once()\
            .with_args(
                [{
                    'taggable_id': 1,
                    'taggable_type': relation.get_parent().__class__.__name__,
                    'tag_id': 2,
                    'foo': 'bar',
                }])\
            .and_return(True)
        mock_query_builder = flexmock()
        relation.get_query().should_receive('get_query').and_return(mock_query_builder)
        mock_query_builder.should_receive('new_query').once().and_return(query)
        relation.should_receive('touch_if_touching').once()

        relation.attach(2, {'foo': 'bar'})

    def test_detach_remove_pivot_table_record(self):
        flexmock(MorphToMany, touch_if_touching=lambda: True)
        relation = self._get_relation()
        query = flexmock()
        query.should_receive('from_').once().with_args('taggables').and_return(query)
        query.should_receive('where').once().with_args('taggable_id', 1).and_return(query)
        query.should_receive('where').once()\
            .with_args('taggable_type', relation.get_parent().__class__.__name__).and_return(query)
        query.should_receive('where_in').once().with_args('tag_id', [1, 2, 3])
        query.should_receive('delete').once().and_return(True)
        mock_query_builder = flexmock()
        relation.get_query().should_receive('get_query').and_return(mock_query_builder)
        mock_query_builder.should_receive('new_query').once().and_return(query)
        relation.should_receive('touch_if_touching').once()

        self.assertTrue(relation.detach([1, 2, 3]))

    def test_detach_clears_all_records_when_no_ids(self):
        flexmock(MorphToMany, touch_if_touching=lambda: True)
        relation = self._get_relation()
        query = flexmock()
        query.should_receive('from_').once().with_args('taggables').and_return(query)
        query.should_receive('where').once().with_args('taggable_id', 1).and_return(query)
        query.should_receive('where').once()\
            .with_args('taggable_type', relation.get_parent().__class__.__name__).and_return(query)
        query.should_receive('where_in').never()
        query.should_receive('delete').once().and_return(True)
        mock_query_builder = flexmock()
        relation.get_query().should_receive('get_query').and_return(mock_query_builder)
        mock_query_builder.should_receive('new_query').once().and_return(query)
        relation.should_receive('touch_if_touching').once()

        self.assertTrue(relation.detach())

    def _get_relation(self):
        builder, parent = self._get_relation_arguments()[:2]

        return MorphToMany(builder, parent, 'taggable', 'taggables', 'taggable_id', 'tag_id')

    def _get_relation_arguments(self):
        parent = flexmock(Model())
        parent.should_receive('get_morph_class').and_return(parent.__class__.__name__)
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

        related.should_receive('get_key_name').and_return('id')
        related.should_receive('get_table').and_return('tags')
        related.should_receive('get_morph_class').and_return(parent.__class__.__name__)

        builder.get_query().should_receive('join').once().with_args('taggables', 'tags.id', '=', 'taggables.tag_id')
        builder.should_receive('where').once().with_args('taggables.taggable_id', '=', 1)
        builder.should_receive('where').once().with_args('taggables.taggable_type', parent.__class__.__name__)

        return builder, parent, 'taggable', 'taggables', 'taggable_id', 'tag_id', 'relation_name', False


class OrmMorphToManyModelStub(Model):

    __guarded__ = []


class OrmMorphToManyModelPivotStub(Model):

    __guarded__ = []

    def __init__(self):
        super(OrmMorphToManyModelPivotStub, self).__init__()

        self.pivot = OrmMorphToManyPivotStub()


class OrmMorphToManyPivotStub(object):
    pass
