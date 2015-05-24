# -*- coding: utf-8 -*-


import arrow
from flexmock import flexmock, flexmock_teardown
from ... import OratorTestCase

from orator.query.builder import QueryBuilder
from orator.orm.builder import Builder
from orator.orm.model import Model
from orator.orm.relations import HasOne


class OrmRelationTestCase(OratorTestCase):

    def tearDown(self):
        flexmock_teardown()

    def test_set_relation_fail(self):
        parent = OrmRelationResetModelStub()
        relation = OrmRelationResetModelStub()
        parent.set_relation('test', relation)
        parent.set_relation('foo', 'bar')
        self.assertFalse('foo' in parent.to_dict())

    def test_touch_method_updates_related_timestamps(self):
        builder = flexmock(Builder, get_model=None, where=None)
        parent = Model()
        parent = flexmock(parent)
        parent.should_receive('get_attribute').with_args('id').and_return(1)
        related = Model()
        related = flexmock(related)
        builder.should_receive('get_model').and_return(related)
        builder.should_receive('where')
        relation = HasOne(Builder(QueryBuilder(None, None, None)), parent, 'foreign_key', 'id')
        related.should_receive('get_table').and_return('table')
        related.should_receive('get_updated_at_column').and_return('updated_at')
        now = arrow.get()
        related.should_receive('fresh_timestamp').and_return(now)
        builder.should_receive('update').once().with_args({'updated_at': now})

        relation.touch()


class OrmRelationResetModelStub(Model):

    def get_query(self):
        return self.new_query().get_query()
