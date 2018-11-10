# -*- coding: utf-8 -*-

from flexmock import flexmock, flexmock_teardown
from orator import DatabaseManager
from orator.connections import Connection
from orator.seeds import Seeder
from cleo import Output, Command as BaseCommand

from .. import OratorTestCase


class SeederTestCase(OratorTestCase):
    def tearDown(self):
        super(SeederTestCase, self).tearDown()
        flexmock_teardown()

    def test_call_resolve_class_and_calls_run(self):
        resolver_mock = flexmock(DatabaseManager)
        resolver_mock.should_receive("connection").and_return({})
        resolver = flexmock(DatabaseManager({}))
        connection = flexmock(Connection(None))
        resolver.should_receive("connection").with_args(None).and_return(connection)
        seeder = Seeder(resolver)
        command = flexmock(Command("foo"))
        command.should_receive("line").once()
        seeder.set_command(command)
        child = flexmock()
        child.__name__ = "foo"
        child.should_receive("set_command").once().with_args(command)
        child.should_receive("set_connection_resolver").once().with_args(resolver)
        child.should_receive("run").once()

        seeder.call(child)


class Command(BaseCommand):

    resolver = "bar"

    def get_output(self):
        return "foo"
