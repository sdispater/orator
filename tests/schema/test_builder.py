# -*- coding: utf-8 -*-

from flexmock import flexmock, flexmock_teardown
from orator.connections import Connection
from orator.schema import SchemaBuilder
from .. import OratorTestCase


class SchemaBuilderTestCase(OratorTestCase):

    def tearDown(self):
        flexmock_teardown()

    def test_has_table_correctly_calls_grammar(self):
        connection = flexmock(Connection(None))
        grammar = flexmock()
        connection.should_receive('get_schema_grammar').and_return(grammar)
        builder = SchemaBuilder(connection)
        grammar.should_receive('compile_table_exists').once().and_return('sql')
        connection.should_receive('get_table_prefix').once().and_return('prefix_')
        connection.should_receive('select').once().with_args('sql', ['prefix_table']).and_return(['prefix_table'])

        self.assertTrue(builder.has_table('table'))
