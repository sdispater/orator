# -*- coding: utf-8 -*-

import arrow
from flexmock import flexmock, flexmock_teardown
from ... import OratorTestCase

from orator.query.builder import QueryBuilder
from orator.query.grammars import QueryGrammar
from orator.query.expression import QueryExpression
from orator.orm.builder import Builder
from orator.orm.model import Model
from orator.orm.relations import MorphOne, MorphMany
from orator.orm.collection import Collection


class OrmMorphTestCase(OratorTestCase):

    def tearDown(self):
        flexmock_teardown()

    def test_morph_one_sets_proper_constraints(self):
        self._get_one_relation()

    def test_morph_one_eager_constraints_are_properly_added(self):
        relation = self._get_one_relation()
        relation.get_query().get_query().should_receive('where_in').once().with_args('table.morph_id', [1, 2])
        relation.get_query().should_receive('where').once()\
            .with_args('table.morph_type', relation.get_parent().__class__.__name__)

        model1 = Model()
        model1.id = 1
        model2 = Model()
        model2.id = 2
        relation.add_eager_constraints([model1, model2])

    def test_morph_many_sets_proper_constraints(self):
        self._get_many_relation()

    def test_morph_many_eager_constraints_are_properly_added(self):
        relation = self._get_many_relation()
        relation.get_query().get_query().should_receive('where_in').once().with_args('table.morph_id', [1, 2])
        relation.get_query().should_receive('where').once()\
            .with_args('table.morph_type', relation.get_parent().__class__.__name__)

        model1 = Model()
        model1.id = 1
        model2 = Model()
        model2.id = 2
        relation.add_eager_constraints([model1, model2])

    def test_create(self):
        relation = self._get_one_relation()
        created = flexmock(Model())
        created.should_receive('set_attribute').once().with_args('morph_id', 1)
        created.should_receive('set_attribute').once()\
            .with_args('morph_type', relation.get_parent().__class__.__name__)
        relation.get_related().should_receive('new_instance').once().with_args({'name': 'john'}).and_return(created)
        created.should_receive('save').once().and_return(True)

        self.assertEqual(created, relation.create(name='john'))

    def test_find_or_new_finds_model(self):
        relation = self._get_one_relation()
        model = flexmock()
        model.foo = 'bar'
        relation.get_query().should_receive('find').once().with_args('foo', ['*']).and_return(model)
        relation.get_related().should_receive('new_instance').never()
        model.should_receive('set_attribute').never()
        model.should_receive('save').never()

        self.assertEqual('bar', relation.find_or_new('foo').foo)

    def test_find_or_new_returns_new_model_with_morph_keys_set(self):
        relation = self._get_one_relation()
        model = flexmock()
        model.foo = 'bar'
        relation.get_query().should_receive('find').once().with_args('foo', ['*']).and_return(None)
        relation.get_related().should_receive('new_instance').once().with_args().and_return(model)
        model.should_receive('set_attribute').once().with_args('morph_id', 1)
        model.should_receive('set_attribute').once().with_args('morph_type', relation.get_parent().__class__.__name__)
        model.should_receive('save').never()

        self.assertEqual('bar', relation.find_or_new('foo').foo)

    def test_first_or_new_returns_first_model(self):
        relation = self._get_one_relation()
        model = flexmock()
        model.foo = 'bar'
        relation.get_query().should_receive('where').once().with_args({'foo': 'bar'}).and_return(relation.get_query())
        relation.get_query().should_receive('first').once().with_args().and_return(model)
        relation.get_related().should_receive('new_instance').never()
        model.should_receive('set_attribute').never()
        model.should_receive('set_attribute').never()
        model.should_receive('save').never()

        self.assertEqual('bar', relation.first_or_new({'foo': 'bar'}).foo)

    def test_first_or_new_returns_new_model_with_morph_keys_set(self):
        relation = self._get_one_relation()
        model = flexmock()
        model.foo = 'bar'
        relation.get_query().should_receive('where').once().with_args({'foo': 'bar'}).and_return(relation.get_query())
        relation.get_query().should_receive('first').once().with_args().and_return(None)
        relation.get_related().should_receive('new_instance').once().with_args().and_return(model)
        model.should_receive('set_attribute').once().with_args('morph_id', 1)
        model.should_receive('set_attribute').once().with_args('morph_type', relation.get_parent().__class__.__name__)
        model.should_receive('save').never()

        self.assertEqual('bar', relation.first_or_new({'foo': 'bar'}).foo)

    def test_first_or_create_returns_first_model(self):
        relation = self._get_one_relation()
        model = flexmock()
        model.foo = 'bar'
        relation.get_query().should_receive('where').once().with_args({'foo': 'bar'}).and_return(relation.get_query())
        relation.get_query().should_receive('first').once().with_args().and_return(model)
        relation.get_related().should_receive('new_instance').never()
        model.should_receive('set_attribute').never()
        model.should_receive('set_attribute').never()
        model.should_receive('save').never()

        self.assertEqual('bar', relation.first_or_create({'foo': 'bar'}).foo)

    def test_first_or_create_creates_new_morph_model(self):
        relation = self._get_one_relation()
        model = flexmock()
        model.foo = 'bar'
        relation.get_query().should_receive('where').once().with_args({'foo': 'bar'}).and_return(relation.get_query())
        relation.get_query().should_receive('first').once().with_args().and_return(None)
        relation.get_related().should_receive('new_instance').once().with_args({'foo': 'bar'}).and_return(model)
        model.should_receive('set_attribute').once().with_args('morph_id', 1)
        model.should_receive('set_attribute').once().with_args('morph_type', relation.get_parent().__class__.__name__)
        model.should_receive('save').once().and_return()

        self.assertEqual('bar', relation.first_or_create({'foo': 'bar'}).foo)

    def test_update_or_create_finds_first_model_and_updates(self):
        relation = self._get_one_relation()
        model = flexmock()
        model.foo = 'bar'
        relation.get_query().should_receive('where').once().with_args({'foo': 'bar'}).and_return(relation.get_query())
        relation.get_query().should_receive('first').once().with_args().and_return(model)
        relation.get_related().should_receive('new_instance').never()
        model.should_receive('set_attribute').never()
        model.should_receive('set_attribute').never()
        model.should_receive('fill').once().with_args({'bar': 'baz'})
        model.should_receive('save').once().and_return(True)

        self.assertEqual('bar', relation.update_or_create({'foo': 'bar'}, {'bar': 'baz'}).foo)

    def test_update_or_create_finds_creates_new_morph_model(self):
        relation = self._get_one_relation()
        model = flexmock()
        model.foo = 'bar'
        relation.get_query().should_receive('where').once().with_args({'foo': 'bar'}).and_return(relation.get_query())
        relation.get_query().should_receive('first').once().with_args().and_return(None)
        relation.get_related().should_receive('new_instance').once().with_args().and_return(model)
        model.should_receive('set_attribute').once().with_args('morph_id', 1)
        model.should_receive('set_attribute').once().with_args('morph_type', relation.get_parent().__class__.__name__)
        model.should_receive('fill').once().with_args({'bar': 'baz'})
        model.should_receive('save').once().and_return(True)

        self.assertEqual('bar', relation.update_or_create({'foo': 'bar'}, {'bar': 'baz'}).foo)

    def _get_many_relation(self):
        flexmock(Builder)
        query = flexmock(QueryBuilder(None, QueryGrammar(), None))
        builder = Builder(query)
        builder.should_receive('where').with_args('table.morph_id', '=', 1)
        related = flexmock(Model())
        builder.should_receive('get_model').and_return(related)
        parent = flexmock(Model())
        parent.should_receive('get_attribute').with_args('id').and_return(1)
        parent.should_receive('get_morph_class').and_return(parent.__class__.__name__)
        builder.should_receive('where').once().with_args('table.morph_type', parent.__class__.__name__)

        return MorphMany(builder, parent, 'table.morph_type', 'table.morph_id', 'id')

    def _get_one_relation(self):
        flexmock(Builder)
        query = flexmock(QueryBuilder(None, QueryGrammar(), None))
        builder = Builder(query)
        builder.should_receive('where').with_args('table.morph_id', '=', 1)
        related = flexmock(Model())
        builder.should_receive('get_model').and_return(related)
        parent = flexmock(Model())
        parent.should_receive('get_attribute').with_args('id').and_return(1)
        parent.should_receive('get_morph_class').and_return(parent.__class__.__name__)
        builder.should_receive('where').once().with_args('table.morph_type', parent.__class__.__name__)

        return MorphOne(builder, parent, 'table.morph_type', 'table.morph_id', 'id')
