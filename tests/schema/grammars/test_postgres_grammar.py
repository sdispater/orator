# -*- coding: utf-8 -*-

from flexmock import flexmock, flexmock_teardown
from orator.connections import Connection
from orator.schema.grammars import PostgresSchemaGrammar
from orator.schema.blueprint import Blueprint
from ... import OratorTestCase


class PostgresSchemaGrammarTestCase(OratorTestCase):

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
            'CREATE TABLE "users" ("id" SERIAL PRIMARY KEY NOT NULL, "email" VARCHAR(255) NOT NULL)',
            statements[0]
        )

        blueprint = Blueprint('users')
        blueprint.increments('id')
        blueprint.string('email')
        statements = blueprint.to_sql(self.get_connection(), self.get_grammar())

        self.assertEqual(1, len(statements))
        expected = [
            'ALTER TABLE "users" ADD COLUMN "id" SERIAL PRIMARY KEY NOT NULL, '
            'ADD COLUMN "email" VARCHAR(255) NOT NULL'
        ]
        self.assertEqual(expected[0], statements[0])

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

    def test_drop_column(self):
        blueprint = Blueprint('users')
        blueprint.drop_column('foo')
        statements = blueprint.to_sql(self.get_connection(), self.get_grammar())

        self.assertEqual(1, len(statements))
        self.assertEqual('ALTER TABLE "users" DROP COLUMN "foo"', statements[0])

        blueprint = Blueprint('users')
        blueprint.drop_column('foo', 'bar')
        statements = blueprint.to_sql(self.get_connection(), self.get_grammar())

        self.assertEqual(1, len(statements))
        self.assertEqual('ALTER TABLE "users" DROP COLUMN "foo", DROP COLUMN "bar"', statements[0])

    def test_drop_primary(self):
        blueprint = Blueprint('users')
        blueprint.drop_primary('foo')
        statements = blueprint.to_sql(self.get_connection(), self.get_grammar())

        self.assertEqual(1, len(statements))
        self.assertEqual('ALTER TABLE "users" DROP CONSTRAINT users_pkey', statements[0])

    def test_drop_unique(self):
        blueprint = Blueprint('users')
        blueprint.drop_unique('foo')
        statements = blueprint.to_sql(self.get_connection(), self.get_grammar())

        self.assertEqual(1, len(statements))
        self.assertEqual('ALTER TABLE "users" DROP CONSTRAINT foo', statements[0])

    def test_drop_index(self):
        blueprint = Blueprint('users')
        blueprint.drop_index('foo')
        statements = blueprint.to_sql(self.get_connection(), self.get_grammar())

        self.assertEqual(1, len(statements))
        self.assertEqual('DROP INDEX foo', statements[0])

    def test_drop_foreign(self):
        blueprint = Blueprint('users')
        blueprint.drop_unique('foo')
        statements = blueprint.to_sql(self.get_connection(), self.get_grammar())

        self.assertEqual(1, len(statements))
        self.assertEqual('ALTER TABLE "users" DROP CONSTRAINT foo', statements[0])

    def test_drop_timestamps(self):
        blueprint = Blueprint('users')
        blueprint.drop_timestamps()
        statements = blueprint.to_sql(self.get_connection(), self.get_grammar())

        self.assertEqual(1, len(statements))
        self.assertEqual('ALTER TABLE "users" DROP COLUMN "created_at", DROP COLUMN "updated_at"', statements[0])

    def test_rename_table(self):
        blueprint = Blueprint('users')
        blueprint.rename('foo')
        statements = blueprint.to_sql(self.get_connection(), self.get_grammar())

        self.assertEqual(1, len(statements))
        self.assertEqual('ALTER TABLE "users" RENAME TO "foo"', statements[0])

    def test_adding_primary_key(self):
        blueprint = Blueprint('users')
        blueprint.primary('foo')
        statements = blueprint.to_sql(self.get_connection(), self.get_grammar())

        self.assertEqual(1, len(statements))
        self.assertEqual('ALTER TABLE "users" ADD PRIMARY KEY ("foo")', statements[0])

    def test_adding_foreign_key(self):
        blueprint = Blueprint('users')
        blueprint.create()
        blueprint.string('foo').primary()
        blueprint.string('order_id')
        blueprint.foreign('order_id').references('id').on('orders')
        statements = blueprint.to_sql(self.get_connection(), self.get_grammar())

        self.assertEqual(3, len(statements))
        expected = [
            'CREATE TABLE "users" ("foo" VARCHAR(255) NOT NULL, "order_id" VARCHAR(255) NOT NULL)',
            'ALTER TABLE "users" ADD CONSTRAINT users_order_id_foreign'
            ' FOREIGN KEY ("order_id") REFERENCES "orders" ("id")',
            'ALTER TABLE "users" ADD PRIMARY KEY ("foo")'
        ]
        self.assertEqual(expected, statements)

    def test_adding_unique_key(self):
        blueprint = Blueprint('users')
        blueprint.unique('foo', 'bar')
        statements = blueprint.to_sql(self.get_connection(), self.get_grammar())

        self.assertEqual(1, len(statements))
        self.assertEqual(
            'ALTER TABLE "users" ADD CONSTRAINT bar UNIQUE ("foo")',
            statements[0]
        )

    def test_adding_index(self):
        blueprint = Blueprint('users')
        blueprint.index(['foo', 'bar'], 'baz')
        statements = blueprint.to_sql(self.get_connection(), self.get_grammar())

        self.assertEqual(1, len(statements))
        self.assertEqual(
            'CREATE INDEX baz ON "users" ("foo", "bar")',
            statements[0]
        )

    def test_adding_incrementing_id(self):
        blueprint = Blueprint('users')
        blueprint.increments('id')
        statements = blueprint.to_sql(self.get_connection(), self.get_grammar())

        self.assertEqual(1, len(statements))
        self.assertEqual(
            'ALTER TABLE "users" ADD COLUMN "id" SERIAL PRIMARY KEY NOT NULL',
            statements[0]
        )

    def test_adding_big_incrementing_id(self):
        blueprint = Blueprint('users')
        blueprint.big_increments('id')
        statements = blueprint.to_sql(self.get_connection(), self.get_grammar())

        self.assertEqual(1, len(statements))
        self.assertEqual(
            'ALTER TABLE "users" ADD COLUMN "id" BIGSERIAL PRIMARY KEY NOT NULL',
            statements[0]
        )

    def test_adding_string(self):
        blueprint = Blueprint('users')
        blueprint.string('foo')
        statements = blueprint.to_sql(self.get_connection(), self.get_grammar())

        self.assertEqual(1, len(statements))
        self.assertEqual(
            'ALTER TABLE "users" ADD COLUMN "foo" VARCHAR(255) NOT NULL',
            statements[0]
        )

        blueprint = Blueprint('users')
        blueprint.string('foo', 100)
        statements = blueprint.to_sql(self.get_connection(), self.get_grammar())

        self.assertEqual(1, len(statements))
        self.assertEqual(
            'ALTER TABLE "users" ADD COLUMN "foo" VARCHAR(100) NOT NULL',
            statements[0]
        )

        blueprint = Blueprint('users')
        blueprint.string('foo', 100).nullable().default('bar')
        statements = blueprint.to_sql(self.get_connection(), self.get_grammar())

        self.assertEqual(1, len(statements))
        self.assertEqual(
            'ALTER TABLE "users" ADD COLUMN "foo" VARCHAR(100) NULL DEFAULT \'bar\'',
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
            'ALTER TABLE "users" ADD COLUMN "foo" BIGINT NOT NULL',
            statements[0]
        )

        blueprint = Blueprint('users')
        blueprint.big_integer('foo', True)
        statements = blueprint.to_sql(self.get_connection(), self.get_grammar())

        self.assertEqual(1, len(statements))
        self.assertEqual(
            'ALTER TABLE "users" ADD COLUMN "foo" BIGSERIAL PRIMARY KEY NOT NULL',
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
            'ALTER TABLE "users" ADD COLUMN "foo" SERIAL PRIMARY KEY NOT NULL',
            statements[0]
        )

    def test_adding_medium_integer(self):
        blueprint = Blueprint('users')
        blueprint.medium_integer('foo')
        statements = blueprint.to_sql(self.get_connection(), self.get_grammar())

        self.assertEqual(1, len(statements))
        self.assertEqual(
            'ALTER TABLE "users" ADD COLUMN "foo" INTEGER NOT NULL',
            statements[0]
        )

        blueprint = Blueprint('users')
        blueprint.medium_integer('foo', True)
        statements = blueprint.to_sql(self.get_connection(), self.get_grammar())

        self.assertEqual(1, len(statements))
        self.assertEqual(
            'ALTER TABLE "users" ADD COLUMN "foo" SERIAL PRIMARY KEY NOT NULL',
            statements[0]
        )

    def test_adding_tiny_integer(self):
        blueprint = Blueprint('users')
        blueprint.tiny_integer('foo')
        statements = blueprint.to_sql(self.get_connection(), self.get_grammar())

        self.assertEqual(1, len(statements))
        self.assertEqual(
            'ALTER TABLE "users" ADD COLUMN "foo" SMALLINT NOT NULL',
            statements[0]
        )

        blueprint = Blueprint('users')
        blueprint.tiny_integer('foo', True)
        statements = blueprint.to_sql(self.get_connection(), self.get_grammar())

        self.assertEqual(1, len(statements))
        self.assertEqual(
            'ALTER TABLE "users" ADD COLUMN "foo" SMALLSERIAL PRIMARY KEY NOT NULL',
            statements[0]
        )

    def test_adding_small_integer(self):
        blueprint = Blueprint('users')
        blueprint.small_integer('foo')
        statements = blueprint.to_sql(self.get_connection(), self.get_grammar())

        self.assertEqual(1, len(statements))
        self.assertEqual(
            'ALTER TABLE "users" ADD COLUMN "foo" SMALLINT NOT NULL',
            statements[0]
        )

        blueprint = Blueprint('users')
        blueprint.small_integer('foo', True)
        statements = blueprint.to_sql(self.get_connection(), self.get_grammar())

        self.assertEqual(1, len(statements))
        self.assertEqual(
            'ALTER TABLE "users" ADD COLUMN "foo" SMALLSERIAL PRIMARY KEY NOT NULL',
            statements[0]
        )

    def test_adding_float(self):
        blueprint = Blueprint('users')
        blueprint.float('foo', 5, 2)
        statements = blueprint.to_sql(self.get_connection(), self.get_grammar())

        self.assertEqual(1, len(statements))
        self.assertEqual(
            'ALTER TABLE "users" ADD COLUMN "foo" DOUBLE PRECISION NOT NULL',
            statements[0]
        )

    def test_adding_double(self):
        blueprint = Blueprint('users')
        blueprint.double('foo', 15, 8)
        statements = blueprint.to_sql(self.get_connection(), self.get_grammar())

        self.assertEqual(1, len(statements))
        self.assertEqual(
            'ALTER TABLE "users" ADD COLUMN "foo" DOUBLE PRECISION NOT NULL',
            statements[0]
        )

    def test_adding_decimal(self):
        blueprint = Blueprint('users')
        blueprint.decimal('foo', 5, 2)
        statements = blueprint.to_sql(self.get_connection(), self.get_grammar())

        self.assertEqual(1, len(statements))
        self.assertEqual(
            'ALTER TABLE "users" ADD COLUMN "foo" DECIMAL(5, 2) NOT NULL',
            statements[0]
        )

    def test_adding_boolean(self):
        blueprint = Blueprint('users')
        blueprint.boolean('foo')
        statements = blueprint.to_sql(self.get_connection(), self.get_grammar())

        self.assertEqual(1, len(statements))
        self.assertEqual(
            'ALTER TABLE "users" ADD COLUMN "foo" BOOLEAN NOT NULL',
            statements[0]
        )

    def test_adding_enum(self):
        blueprint = Blueprint('users')
        blueprint.enum('foo', ['bar', 'baz'])
        statements = blueprint.to_sql(self.get_connection(), self.get_grammar())

        self.assertEqual(1, len(statements))
        self.assertEqual(
            'ALTER TABLE "users" ADD COLUMN "foo" VARCHAR(255) CHECK ("foo" IN (\'bar\', \'baz\')) NOT NULL',
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
            'ALTER TABLE "users" ADD COLUMN "foo" TIMESTAMP(0) WITHOUT TIME ZONE NOT NULL',
            statements[0]
        )

    def test_adding_time(self):
        blueprint = Blueprint('users')
        blueprint.time('foo')
        statements = blueprint.to_sql(self.get_connection(), self.get_grammar())

        self.assertEqual(1, len(statements))
        self.assertEqual(
            'ALTER TABLE "users" ADD COLUMN "foo" TIME(0) WITHOUT TIME ZONE NOT NULL',
            statements[0]
        )

    def test_adding_timestamp(self):
        blueprint = Blueprint('users')
        blueprint.timestamp('foo')
        statements = blueprint.to_sql(self.get_connection(), self.get_grammar())

        self.assertEqual(1, len(statements))
        self.assertEqual(
            'ALTER TABLE "users" ADD COLUMN "foo" TIMESTAMP(0) WITHOUT TIME ZONE NOT NULL',
            statements[0]
        )

    def test_adding_timestamps(self):
        blueprint = Blueprint('users')
        blueprint.timestamps()
        statements = blueprint.to_sql(self.get_connection(), self.get_grammar())

        self.assertEqual(1, len(statements))
        expected = [
            'ALTER TABLE "users" ADD COLUMN "created_at" TIMESTAMP(0) WITHOUT TIME ZONE NOT NULL, '
            'ADD COLUMN "updated_at" TIMESTAMP(0) WITHOUT TIME ZONE NOT NULL'
        ]
        self.assertEqual(
            expected[0],
            statements[0]
        )

    def test_adding_binary(self):
        blueprint = Blueprint('users')
        blueprint.binary('foo')
        statements = blueprint.to_sql(self.get_connection(), self.get_grammar())

        self.assertEqual(1, len(statements))
        self.assertEqual(
            'ALTER TABLE "users" ADD COLUMN "foo" BYTEA NOT NULL',
            statements[0]
        )

    def get_connection(self):
        return flexmock(Connection(None))

    def get_grammar(self):
        return PostgresSchemaGrammar()
