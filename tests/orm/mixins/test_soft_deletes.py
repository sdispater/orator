# -*- coding: utf-8 -*-

import datetime
import arrow
from flexmock import flexmock, flexmock_teardown
from orator import Model, SoftDeletes
from orator.orm import Builder
from orator.query import QueryBuilder
from ... import OratorTestCase


t = arrow.get().naive


class SoftDeletesTestCase(OratorTestCase):

    def tearDown(self):
        flexmock_teardown()

    def test_delete_sets_soft_deleted_column(self):
        model = flexmock(SoftDeleteModelStub())
        model.set_exists(True)
        builder = flexmock(Builder)
        query_builder = flexmock(QueryBuilder(None, None, None))
        query = Builder(query_builder)
        model.should_receive('new_query').and_return(query)
        builder.should_receive('where').once().with_args('id', 1).and_return(query)
        builder.should_receive('update').once().with_args({'deleted_at': t})
        model.delete()

        self.assertIsInstance(model.deleted_at, datetime.datetime)

    def test_restore(self):
        model = flexmock(SoftDeleteModelStub())
        model.set_exists(True)
        model.should_receive('save').once()

        model.restore()

        self.assertIsNone(model.deleted_at)


class SoftDeleteModelStub(Model, SoftDeletes):

    def get_key(self):
        return 1

    def get_key_name(self):
        return 'id'

    def from_datetime(self, value):
        return t
