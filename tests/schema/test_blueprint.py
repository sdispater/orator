# -*- coding: utf-8 -*-

from flexmock import flexmock, flexmock_teardown
from orator.schema import Blueprint
from orator.schema.grammars import SchemaGrammar
from orator.connections import Connection
from .. import OratorTestCase


class SchemaBuilderTestCase(OratorTestCase):

    def tearDown(self):
        flexmock_teardown()

    def test_to_sql_runs_commands_from_blueprint(self):
        conn = flexmock(Connection(None))
        conn.should_receive('statement').once().with_args('foo')
        conn.should_receive('statement').once().with_args('bar')
        grammar = flexmock(SchemaGrammar())
        blueprint = flexmock(Blueprint('table'))
        blueprint.should_receive('to_sql').once().with_args(conn, grammar).and_return(['foo', 'bar'])

        blueprint.build(conn, grammar)

    def test_index_default_names(self):
        blueprint = Blueprint('users')
        blueprint.unique(['foo', 'bar'])
        commands = blueprint.get_commands()
        self.assertEqual('users_foo_bar_unique', commands[0].index)

        blueprint = Blueprint('users')
        blueprint.index('foo')
        commands = blueprint.get_commands()
        self.assertEqual('users_foo_index', commands[0].index)

    def test_drop_index_default_names(self):
        blueprint = Blueprint('users')
        blueprint.drop_unique(['foo', 'bar'])
        commands = blueprint.get_commands()
        self.assertEqual('users_foo_bar_unique', commands[0].index)

        blueprint = Blueprint('users')
        blueprint.drop_index(['foo'])
        commands = blueprint.get_commands()
        self.assertEqual('users_foo_index', commands[0].index)
