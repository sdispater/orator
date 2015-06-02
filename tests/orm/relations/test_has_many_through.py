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
from orator.orm.relations import HasManyThrough
from orator.orm.collection import Collection


class OrmHasManyThroughTestCase(OratorTestCase):

    def tearDown(self):
        flexmock_teardown()

    def test_relation_is_properly_initialized(self):
        relation = self._get_relation()
        model = flexmock(Model())
        relation.get_related().should_receive('new_collection').replace_with(lambda l=None: Collection(l or []))
        model.should_receive('set_relation').once().with_args('foo', Collection)
        models = relation.init_relation([model], 'foo')

        self.assertEqual([model], models)

    def test_eager_constraints_are_properly_added(self):
        relation = self._get_relation()
        relation.get_query().get_query().should_receive('where_in').once().with_args('users.country_id', [1, 2])
        model1 = OrmHasManyThroughModelStub()
        model1.id = 1
        model2 = OrmHasManyThroughModelStub()
        model2.id = 2
        relation.add_eager_constraints([model1, model2])

    def test_models_are_properly_matched_to_parents(self):
        relation = self._get_relation()

        result1 = OrmHasManyThroughModelStub()
        result1.country_id = 1
        result2 = OrmHasManyThroughModelStub()
        result2.country_id = 2
        result3 = OrmHasManyThroughModelStub()
        result3.country_id = 2

        model1 = OrmHasManyThroughModelStub()
        model1.id = 1
        model2 = OrmHasManyThroughModelStub()
        model2.id = 2
        model3 = OrmHasManyThroughModelStub()
        model3.id = 3

        relation.get_related().should_receive('new_collection').replace_with(lambda l=None: Collection(l or []))
        relation.get_query().should_receive('where').with_args('users.country_id', '=', 2)
        relation.get_query().should_receive('where').with_args('users.country_id', '=', 3)
        models = relation.match([model1, model2, model3], Collection([result1, result2, result3]), 'foo')

        self.assertEqual(1, models[0].foo[0].country_id)
        self.assertEqual(1, len(models[0].foo))
        self.assertEqual(2, models[1].foo[0].country_id)
        self.assertEqual(2, models[1].foo[1].country_id)
        self.assertEqual(2, len(models[1].foo))
        self.assertTrue(models[2].foo.is_empty())

    def test_get(self):
        relation = self._get_relation()

        query = relation.get_query()
        query.get_query().should_receive('add_select').once().with_args('posts.*', 'users.country_id').and_return(query)
        query.should_receive('get_models').and_return([])

        relation.get()

    def _get_relation(self):
        flexmock(Builder)
        query = flexmock(QueryBuilder(None, QueryGrammar(), None))
        builder = Builder(query)
        builder.get_query().should_receive('join').at_least().once().with_args('users', 'users.id', '=', 'posts.user_id')
        builder.should_receive('where').with_args('users.country_id', '=', 1)
        country = flexmock(Model())
        country.should_receive('get_key').and_return(1)
        country.should_receive('get_foreign_key').and_return('country_id')
        user = flexmock(Model())
        user.should_receive('get_table').and_return('users')
        user.should_receive('get_qualified_key_name').and_return('users.id')
        post = flexmock(Model())
        post.should_receive('get_table').and_return('posts')
        builder.should_receive('get_model').and_return(post)

        post.should_receive('new_query').and_return(builder)

        user.should_receive('get_key').and_return(1)
        user.should_receive('get_created_at_column').and_return('created_at')
        user.should_receive('get_updated_at_column').and_return('updated_at')

        parent = flexmock(Model())
        parent.should_receive('get_attribute').with_args('id').and_return(1)
        parent.should_receive('get_created_at_column').and_return('created_at')
        parent.should_receive('get_updated_at_column').and_return('updated_at')
        parent.should_receive('new_query').and_return(builder)

        return HasManyThrough(builder, country, user, 'country_id', 'user_id')


class OrmHasManyThroughModelStub(Model):

    pass
