# -*- coding: utf-8 -*-

from flexmock import flexmock, flexmock_teardown
from orator.connections import Connection
from orator.schema.grammars import SQLiteSchemaGrammar
from orator.schema.blueprint import Blueprint
from ... import OratorTestCase


class SqliteSchemaGrammarTestCase(OratorTestCase):

    def tearDown(self):
        flexmock_teardown()

    def test_basic_create(self):
        blueprint = Blueprint('users')
        blueprint.create()
        blueprint.increments('id')
        blueprint.string('email')
        statements = blueprint.to_sql(self.get_connection(), self.get_grammar())

        self.assertEqual(1, len(statements))
        self.assertEqual(
            'CREATE TABLE "users" ("id" INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT, "email" VARCHAR NOT NULL)',
            statements[0]
        )

        blueprint = Blueprint('users')
        blueprint.increments('id')
        blueprint.string('email')
        statements = blueprint.to_sql(self.get_connection(), self.get_grammar())

        self.assertEqual(2, len(statements))
        expected = [
            'ALTER TABLE "users" ADD COLUMN "id" INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT',
            'ALTER TABLE "users" ADD COLUMN "email" VARCHAR NOT NULL'
        ]
        self.assertEqual(expected, statements)

    def test_drop_table(self):
        blueprint = Blueprint('users')
        blueprint.drop()
        statements = blueprint.to_sql(self.get_connection(), self.get_grammar())

        self.assertEqual(1, len(statements))
        self.assertEqual('DROP TABLE "users"', statements[0])

    def test_drop_table_if_exists(self):
        blueprint = Blueprint('users')
        blueprint.drop_if_exists()
        statements = blueprint.to_sql(self.get_connection(), self.get_grammar())

        self.assertEqual(1, len(statements))
        self.assertEqual('DROP TABLE IF EXISTS "users"', statements[0])

    def test_drop_unique(self):
        blueprint = Blueprint('users')
        blueprint.drop_unique('foo')
        statements = blueprint.to_sql(self.get_connection(), self.get_grammar())

        self.assertEqual(1, len(statements))
        self.assertEqual('DROP INDEX foo', statements[0])

    def test_drop_index(self):
        blueprint = Blueprint('users')
        blueprint.drop_index('foo')
        statements = blueprint.to_sql(self.get_connection(), self.get_grammar())

        self.assertEqual(1, len(statements))
        self.assertEqual('DROP INDEX foo', statements[0])

    def test_rename_table(self):
        blueprint = Blueprint('users')
        blueprint.rename('foo')
        statements = blueprint.to_sql(self.get_connection(), self.get_grammar())

        self.assertEqual(1, len(statements))
        self.assertEqual('ALTER TABLE "users" RENAME TO "foo"', statements[0])

    def test_adding_foreign_key(self):
        blueprint = Blueprint('users')
        blueprint.create()
        blueprint.string('foo').primary()
        blueprint.string('order_id')
        blueprint.foreign('order_id').references('id').on('orders')
        statements = blueprint.to_sql(self.get_connection(), self.get_grammar())

        self.assertEqual(1, len(statements))
        expected = 'CREATE TABLE "users" ("foo" VARCHAR NOT NULL, "order_id" VARCHAR NOT NULL, ' \
                   'FOREIGN KEY("order_id") REFERENCES "orders"("id"), PRIMARY KEY ("foo"))'
        self.assertEqual(expected, statements[0])

    def test_adding_unique_key(self):
        blueprint = Blueprint('users')
        blueprint.unique('foo', 'bar')
        statements = blueprint.to_sql(self.get_connection(), self.get_grammar())

        self.assertEqual(1, len(statements))
        self.assertEqual(
            'CREATE UNIQUE INDEX bar ON "users" ("foo")',
            statements[0]
        )

    def test_adding_index(self):
        blueprint = Blueprint('users')
        blueprint.index('foo', 'bar')
        statements = blueprint.to_sql(self.get_connection(), self.get_grammar())

        self.assertEqual(1, len(statements))
        self.assertEqual(
            'CREATE INDEX bar ON "users" ("foo")',
            statements[0]
        )

    def test_adding_incrementing_id(self):
        blueprint = Blueprint('users')
        blueprint.increments('id')
        statements = blueprint.to_sql(self.get_connection(), self.get_grammar())

        self.assertEqual(1, len(statements))
        self.assertEqual(
            'ALTER TABLE "users" ADD COLUMN "id" INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT',
            statements[0]
        )

    def test_adding_big_incrementing_id(self):
        blueprint = Blueprint('users')
        blueprint.big_increments('id')
        statements = blueprint.to_sql(self.get_connection(), self.get_grammar())

        self.assertEqual(1, len(statements))
        self.assertEqual(
            'ALTER TABLE "users" ADD COLUMN "id" INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT',
            statements[0]
        )

    def test_adding_string(self):
        blueprint = Blueprint('users')
        blueprint.string('foo')
        statements = blueprint.to_sql(self.get_connection(), self.get_grammar())

        self.assertEqual(1, len(statements))
        self.assertEqual(
            'ALTER TABLE "users" ADD COLUMN "foo" VARCHAR NOT NULL',
            statements[0]
        )

        blueprint = Blueprint('users')
        blueprint.string('foo', 100)
        statements = blueprint.to_sql(self.get_connection(), self.get_grammar())

        self.assertEqual(1, len(statements))
        self.assertEqual(
            'ALTER TABLE "users" ADD COLUMN "foo" VARCHAR NOT NULL',
            statements[0]
        )

        blueprint = Blueprint('users')
        blueprint.string('foo', 100).nullable().default('bar')
        statements = blueprint.to_sql(self.get_connection(), self.get_grammar())

        self.assertEqual(1, len(statements))
        self.assertEqual(
            'ALTER TABLE "users" ADD COLUMN "foo" VARCHAR NULL DEFAULT \'bar\'',
            statements[0]
        )

    def test_adding_text(self):
        blueprint = Blueprint('users')
        blueprint.text('foo')
        statements = blueprint.to_sql(self.get_connection(), self.get_grammar())

        self.assertEqual(1, len(statements))
        self.assertEqual(
            'ALTER TABLE "users" ADD COLUMN "foo" TEXT NOT NULL',
            statements[0]
        )

    def test_adding_big_integer(self):
        blueprint = Blueprint('users')
        blueprint.big_integer('foo')
        statements = blueprint.to_sql(self.get_connection(), self.get_grammar())

        self.assertEqual(1, len(statements))
        self.assertEqual(
            'ALTER TABLE "users" ADD COLUMN "foo" INTEGER NOT NULL',
            statements[0]
        )

        blueprint = Blueprint('users')
        blueprint.big_integer('foo', True)
        statements = blueprint.to_sql(self.get_connection(), self.get_grammar())

        self.assertEqual(1, len(statements))
        self.assertEqual(
            'ALTER TABLE "users" ADD COLUMN "foo" INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT',
            statements[0]
        )

    def test_adding_integer(self):
        blueprint = Blueprint('users')
        blueprint.integer('foo')
        statements = blueprint.to_sql(self.get_connection(), self.get_grammar())

        self.assertEqual(1, len(statements))
        self.assertEqual(
            'ALTER TABLE "users" ADD COLUMN "foo" INTEGER NOT NULL',
            statements[0]
        )

        blueprint = Blueprint('users')
        blueprint.integer('foo', True)
        statements = blueprint.to_sql(self.get_connection(), self.get_grammar())

        self.assertEqual(1, len(statements))
        self.assertEqual(
            'ALTER TABLE "users" ADD COLUMN "foo" INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT',
            statements[0]
        )

    def test_adding_medium_integer(self):
        blueprint = Blueprint('users')
        blueprint.integer('foo')
        statements = blueprint.to_sql(self.get_connection(), self.get_grammar())

        self.assertEqual(1, len(statements))
        self.assertEqual(
            'ALTER TABLE "users" ADD COLUMN "foo" INTEGER NOT NULL',
            statements[0]
        )

    def test_adding_tiny_integer(self):
        blueprint = Blueprint('users')
        blueprint.integer('foo')
        statements = blueprint.to_sql(self.get_connection(), self.get_grammar())

        self.assertEqual(1, len(statements))
        self.assertEqual(
            'ALTER TABLE "users" ADD COLUMN "foo" INTEGER NOT NULL',
            statements[0]
        )

    def test_adding_small_integer(self):
        blueprint = Blueprint('users')
        blueprint.integer('foo')
        statements = blueprint.to_sql(self.get_connection(), self.get_grammar())

        self.assertEqual(1, len(statements))
        self.assertEqual(
            'ALTER TABLE "users" ADD COLUMN "foo" INTEGER NOT NULL',
            statements[0]
        )

    def test_adding_float(self):
        blueprint = Blueprint('users')
        blueprint.float('foo', 5, 2)
        statements = blueprint.to_sql(self.get_connection(), self.get_grammar())

        self.assertEqual(1, len(statements))
        self.assertEqual(
            'ALTER TABLE "users" ADD COLUMN "foo" FLOAT NOT NULL',
            statements[0]
        )

    def test_adding_double(self):
        blueprint = Blueprint('users')
        blueprint.double('foo', 15, 8)
        statements = blueprint.to_sql(self.get_connection(), self.get_grammar())

        self.assertEqual(1, len(statements))
        self.assertEqual(
            'ALTER TABLE "users" ADD COLUMN "foo" FLOAT NOT NULL',
            statements[0]
        )

    def test_adding_decimal(self):
        blueprint = Blueprint('users')
        blueprint.decimal('foo', 5, 2)
        statements = blueprint.to_sql(self.get_connection(), self.get_grammar())

        self.assertEqual(1, len(statements))
        self.assertEqual(
            'ALTER TABLE "users" ADD COLUMN "foo" NUMERIC NOT NULL',
            statements[0]
        )

    def test_adding_boolean(self):
        blueprint = Blueprint('users')
        blueprint.boolean('foo')
        statements = blueprint.to_sql(self.get_connection(), self.get_grammar())

        self.assertEqual(1, len(statements))
        self.assertEqual(
            'ALTER TABLE "users" ADD COLUMN "foo" TINYINT NOT NULL',
            statements[0]
        )

    def test_adding_enum(self):
        blueprint = Blueprint('users')
        blueprint.enum('foo', ['bar', 'baz'])
        statements = blueprint.to_sql(self.get_connection(), self.get_grammar())

        self.assertEqual(1, len(statements))
        self.assertEqual(
            'ALTER TABLE "users" ADD COLUMN "foo" VARCHAR NOT NULL',
            statements[0]
        )

    def test_adding_date(self):
        blueprint = Blueprint('users')
        blueprint.date('foo')
        statements = blueprint.to_sql(self.get_connection(), self.get_grammar())

        self.assertEqual(1, len(statements))
        self.assertEqual(
            'ALTER TABLE "users" ADD COLUMN "foo" DATE NOT NULL',
            statements[0]
        )

    def test_adding_datetime(self):
        blueprint = Blueprint('users')
        blueprint.datetime('foo')
        statements = blueprint.to_sql(self.get_connection(), self.get_grammar())

        self.assertEqual(1, len(statements))
        self.assertEqual(
            'ALTER TABLE "users" ADD COLUMN "foo" DATETIME NOT NULL',
            statements[0]
        )

    def test_adding_time(self):
        blueprint = Blueprint('users')
        blueprint.time('foo')
        statements = blueprint.to_sql(self.get_connection(), self.get_grammar())

        self.assertEqual(1, len(statements))
        self.assertEqual(
            'ALTER TABLE "users" ADD COLUMN "foo" TIME NOT NULL',
            statements[0]
        )

    def test_adding_timestamp(self):
        blueprint = Blueprint('users')
        blueprint.timestamp('foo')
        statements = blueprint.to_sql(self.get_connection(), self.get_grammar())

        self.assertEqual(1, len(statements))
        self.assertEqual(
            'ALTER TABLE "users" ADD COLUMN "foo" DATETIME NOT NULL',
            statements[0]
        )

    def test_adding_timestamps(self):
        blueprint = Blueprint('users')
        blueprint.timestamps()
        statements = blueprint.to_sql(self.get_connection(), self.get_grammar())

        self.assertEqual(2, len(statements))
        expected = [
            'ALTER TABLE "users" ADD COLUMN "created_at" DATETIME NOT NULL',
            'ALTER TABLE "users" ADD COLUMN "updated_at" DATETIME NOT NULL'
        ]
        self.assertEqual(
            expected,
            statements
        )

    def test_adding_binary(self):
        blueprint = Blueprint('users')
        blueprint.binary('foo')
        statements = blueprint.to_sql(self.get_connection(), self.get_grammar())

        self.assertEqual(1, len(statements))
        self.assertEqual(
            'ALTER TABLE "users" ADD COLUMN "foo" BLOB NOT NULL',
            statements[0]
        )

    def get_connection(self):
        return flexmock(Connection(None))

    def get_grammar(self):
        return SQLiteSchemaGrammar()
