# -*- coding: utf-8 -*-

from flexmock import flexmock, flexmock_teardown
from orator.connections import Connection
from orator.schema.grammars import MySqlSchemaGrammar
from orator.schema.blueprint import Blueprint
from ... import OratorTestCase


class MySqlSchemaGrammarTestCase(OratorTestCase):

    def tearDown(self):
        flexmock_teardown()

    def test_basic_create(self):
        blueprint = Blueprint('users')
        blueprint.create()
        blueprint.increments('id')
        blueprint.string('email')

        conn = self.get_connection()
        conn.should_receive('get_config').once().with_args('charset').and_return('utf8')
        conn.should_receive('get_config').once().with_args('collation').and_return('utf8_unicode_ci')

        statements = blueprint.to_sql(conn, self.get_grammar())

        self.assertEqual(1, len(statements))
        self.assertEqual(
            'CREATE TABLE `users` ('
            '`id` INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY, '
            '`email` VARCHAR(255) NOT NULL) '
            'DEFAULT CHARACTER SET utf8 COLLATE utf8_unicode_ci',
            statements[0]
        )

        blueprint = Blueprint('users')
        blueprint.create()
        blueprint.increments('id')
        blueprint.string('email')

        conn = self.get_connection()
        conn.should_receive('get_config').and_return(None)

        statements = blueprint.to_sql(conn, self.get_grammar())

        self.assertEqual(1, len(statements))
        self.assertEqual(
            'CREATE TABLE `users` ('
            '`id` INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY, '
            '`email` VARCHAR(255) NOT NULL)',
            statements[0]
        )

    def test_charset_collation_create(self):
        blueprint = Blueprint('users')
        blueprint.create()
        blueprint.increments('id')
        blueprint.string('email')
        blueprint.charset = 'utf8mb4'
        blueprint.collation = 'utf8mb4_unicode_ci'

        conn = self.get_connection()

        statements = blueprint.to_sql(conn, self.get_grammar())

        self.assertEqual(1, len(statements))
        self.assertEqual(
            'CREATE TABLE `users` ('
            '`id` INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY, '
            '`email` VARCHAR(255) NOT NULL) '
            'DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci',
            statements[0]
        )

    def test_basic_create_with_prefix(self):
        blueprint = Blueprint('users')
        blueprint.create()
        blueprint.increments('id')
        blueprint.string('email')
        grammar = self.get_grammar()
        grammar.set_table_prefix('prefix_')

        conn = self.get_connection()
        conn.should_receive('get_config').and_return(None)

        statements = blueprint.to_sql(conn, grammar)

        self.assertEqual(1, len(statements))
        self.assertEqual(
            'CREATE TABLE `prefix_users` ('
            '`id` INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY, '
            '`email` VARCHAR(255) NOT NULL)',
            statements[0]
        )

    def test_drop_table(self):
        blueprint = Blueprint('users')
        blueprint.drop()
        statements = blueprint.to_sql(self.get_connection(), self.get_grammar())

        self.assertEqual(1, len(statements))
        self.assertEqual('DROP TABLE `users`', statements[0])

    def test_drop_table_if_exists(self):
        blueprint = Blueprint('users')
        blueprint.drop_if_exists()
        statements = blueprint.to_sql(self.get_connection(), self.get_grammar())

        self.assertEqual(1, len(statements))
        self.assertEqual('DROP TABLE IF EXISTS `users`', statements[0])

    def test_drop_column(self):
        blueprint = Blueprint('users')
        blueprint.drop_column('foo')
        statements = blueprint.to_sql(self.get_connection(), self.get_grammar())

        self.assertEqual(1, len(statements))
        self.assertEqual('ALTER TABLE `users` DROP `foo`', statements[0])

        blueprint = Blueprint('users')
        blueprint.drop_column('foo', 'bar')
        statements = blueprint.to_sql(self.get_connection(), self.get_grammar())

        self.assertEqual(1, len(statements))
        self.assertEqual('ALTER TABLE `users` DROP `foo`, DROP `bar`', statements[0])

    def test_drop_primary(self):
        blueprint = Blueprint('users')
        blueprint.drop_primary('foo')
        statements = blueprint.to_sql(self.get_connection(), self.get_grammar())

        self.assertEqual(1, len(statements))
        self.assertEqual('ALTER TABLE `users` DROP PRIMARY KEY', statements[0])

    def test_drop_unique(self):
        blueprint = Blueprint('users')
        blueprint.drop_unique('foo')
        statements = blueprint.to_sql(self.get_connection(), self.get_grammar())

        self.assertEqual(1, len(statements))
        self.assertEqual('ALTER TABLE `users` DROP INDEX foo', statements[0])

    def test_drop_index(self):
        blueprint = Blueprint('users')
        blueprint.drop_index('foo')
        statements = blueprint.to_sql(self.get_connection(), self.get_grammar())

        self.assertEqual(1, len(statements))
        self.assertEqual('ALTER TABLE `users` DROP INDEX foo', statements[0])

    def test_drop_foreign(self):
        blueprint = Blueprint('users')
        blueprint.drop_foreign('foo')
        statements = blueprint.to_sql(self.get_connection(), self.get_grammar())

        self.assertEqual(1, len(statements))
        self.assertEqual('ALTER TABLE `users` DROP FOREIGN KEY foo', statements[0])

    def test_drop_timestamps(self):
        blueprint = Blueprint('users')
        blueprint.drop_timestamps()
        statements = blueprint.to_sql(self.get_connection(), self.get_grammar())

        self.assertEqual(1, len(statements))
        self.assertEqual('ALTER TABLE `users` DROP `created_at`, DROP `updated_at`', statements[0])

    def test_rename_table(self):
        blueprint = Blueprint('users')
        blueprint.rename('foo')
        statements = blueprint.to_sql(self.get_connection(), self.get_grammar())

        self.assertEqual(1, len(statements))
        self.assertEqual('RENAME TABLE `users` TO `foo`', statements[0])

    def test_adding_primary_key(self):
        blueprint = Blueprint('users')
        blueprint.primary('foo', 'bar')
        statements = blueprint.to_sql(self.get_connection(), self.get_grammar())

        self.assertEqual(1, len(statements))
        self.assertEqual('ALTER TABLE `users` ADD PRIMARY KEY bar(`foo`)', statements[0])

    def test_adding_foreign_key(self):
        blueprint = Blueprint('users')
        blueprint.foreign('order_id').references('id').on('orders')
        statements = blueprint.to_sql(self.get_connection(), self.get_grammar())

        self.assertEqual(1, len(statements))
        expected = [
            'ALTER TABLE `users` ADD CONSTRAINT users_order_id_foreign '
            'FOREIGN KEY (`order_id`) REFERENCES `orders` (`id`)'
        ]
        self.assertEqual(expected, statements)

    def test_adding_unique_key(self):
        blueprint = Blueprint('users')
        blueprint.unique('foo', 'bar')
        statements = blueprint.to_sql(self.get_connection(), self.get_grammar())

        self.assertEqual(1, len(statements))
        self.assertEqual(
            'ALTER TABLE `users` ADD UNIQUE bar(`foo`)',
            statements[0]
        )

    def test_adding_index(self):
        blueprint = Blueprint('users')
        blueprint.index(['foo', 'bar'], 'baz')
        statements = blueprint.to_sql(self.get_connection(), self.get_grammar())

        self.assertEqual(1, len(statements))
        self.assertEqual(
            'ALTER TABLE `users` ADD INDEX baz(`foo`, `bar`)',
            statements[0]
        )

    def test_adding_incrementing_id(self):
        blueprint = Blueprint('users')
        blueprint.increments('id')
        statements = blueprint.to_sql(self.get_connection(), self.get_grammar())

        self.assertEqual(1, len(statements))
        self.assertEqual(
            'ALTER TABLE `users` ADD `id` INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY',
            statements[0]
        )

    def test_adding_big_incrementing_id(self):
        blueprint = Blueprint('users')
        blueprint.big_increments('id')
        statements = blueprint.to_sql(self.get_connection(), self.get_grammar())

        self.assertEqual(1, len(statements))
        self.assertEqual(
            'ALTER TABLE `users` ADD `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY',
            statements[0]
        )
        
    def test_adding_column_after_another(self):
        blueprint = Blueprint('users')
        blueprint.string('name').after('foo')
        
        statements = blueprint.to_sql(self.get_connection(), self.get_grammar())

        self.assertEqual(1, len(statements))
        self.assertEqual(
            'ALTER TABLE `users` ADD `name` VARCHAR(255) NOT NULL AFTER `foo`',
            statements[0]
        )

    def test_adding_string(self):
        blueprint = Blueprint('users')
        blueprint.string('foo')
        statements = blueprint.to_sql(self.get_connection(), self.get_grammar())

        self.assertEqual(1, len(statements))
        self.assertEqual(
            'ALTER TABLE `users` ADD `foo` VARCHAR(255) NOT NULL',
            statements[0]
        )

        blueprint = Blueprint('users')
        blueprint.string('foo', 100)
        statements = blueprint.to_sql(self.get_connection(), self.get_grammar())

        self.assertEqual(1, len(statements))
        self.assertEqual(
            'ALTER TABLE `users` ADD `foo` VARCHAR(100) NOT NULL',
            statements[0]
        )

        blueprint = Blueprint('users')
        blueprint.string('foo', 100).nullable().default('bar')
        statements = blueprint.to_sql(self.get_connection(), self.get_grammar())

        self.assertEqual(1, len(statements))
        self.assertEqual(
            'ALTER TABLE `users` ADD `foo` VARCHAR(100) NULL DEFAULT \'bar\'',
            statements[0]
        )

    def test_adding_text(self):
        blueprint = Blueprint('users')
        blueprint.text('foo')
        statements = blueprint.to_sql(self.get_connection(), self.get_grammar())

        self.assertEqual(1, len(statements))
        self.assertEqual(
            'ALTER TABLE `users` ADD `foo` TEXT NOT NULL',
            statements[0]
        )

    def test_adding_big_integer(self):
        blueprint = Blueprint('users')
        blueprint.big_integer('foo')
        statements = blueprint.to_sql(self.get_connection(), self.get_grammar())

        self.assertEqual(1, len(statements))
        self.assertEqual(
            'ALTER TABLE `users` ADD `foo` BIGINT NOT NULL',
            statements[0]
        )

        blueprint = Blueprint('users')
        blueprint.big_integer('foo', True)
        statements = blueprint.to_sql(self.get_connection(), self.get_grammar())

        self.assertEqual(1, len(statements))
        self.assertEqual(
            'ALTER TABLE `users` ADD `foo` BIGINT NOT NULL AUTO_INCREMENT PRIMARY KEY',
            statements[0]
        )

    def test_adding_integer(self):
        blueprint = Blueprint('users')
        blueprint.integer('foo')
        statements = blueprint.to_sql(self.get_connection(), self.get_grammar())

        self.assertEqual(1, len(statements))
        self.assertEqual(
            'ALTER TABLE `users` ADD `foo` INT NOT NULL',
            statements[0]
        )

        blueprint = Blueprint('users')
        blueprint.integer('foo', True)
        statements = blueprint.to_sql(self.get_connection(), self.get_grammar())

        self.assertEqual(1, len(statements))
        self.assertEqual(
            'ALTER TABLE `users` ADD `foo` INT NOT NULL AUTO_INCREMENT PRIMARY KEY',
            statements[0]
        )

    def test_adding_medium_integer(self):
        blueprint = Blueprint('users')
        blueprint.medium_integer('foo')
        statements = blueprint.to_sql(self.get_connection(), self.get_grammar())

        self.assertEqual(1, len(statements))
        self.assertEqual(
            'ALTER TABLE `users` ADD `foo` MEDIUMINT NOT NULL',
            statements[0]
        )

        blueprint = Blueprint('users')
        blueprint.medium_integer('foo', True)
        statements = blueprint.to_sql(self.get_connection(), self.get_grammar())

        self.assertEqual(1, len(statements))
        self.assertEqual(
            'ALTER TABLE `users` ADD `foo` MEDIUMINT NOT NULL AUTO_INCREMENT PRIMARY KEY',
            statements[0]
        )

    def test_adding_tiny_integer(self):
        blueprint = Blueprint('users')
        blueprint.tiny_integer('foo')
        statements = blueprint.to_sql(self.get_connection(), self.get_grammar())

        self.assertEqual(1, len(statements))
        self.assertEqual(
            'ALTER TABLE `users` ADD `foo` TINYINT NOT NULL',
            statements[0]
        )

        blueprint = Blueprint('users')
        blueprint.tiny_integer('foo', True)
        statements = blueprint.to_sql(self.get_connection(), self.get_grammar())

        self.assertEqual(1, len(statements))
        self.assertEqual(
            'ALTER TABLE `users` ADD `foo` TINYINT NOT NULL AUTO_INCREMENT PRIMARY KEY',
            statements[0]
        )

    def test_adding_small_integer(self):
        blueprint = Blueprint('users')
        blueprint.small_integer('foo')
        statements = blueprint.to_sql(self.get_connection(), self.get_grammar())

        self.assertEqual(1, len(statements))
        self.assertEqual(
            'ALTER TABLE `users` ADD `foo` SMALLINT NOT NULL',
            statements[0]
        )

        blueprint = Blueprint('users')
        blueprint.small_integer('foo', True)
        statements = blueprint.to_sql(self.get_connection(), self.get_grammar())

        self.assertEqual(1, len(statements))
        self.assertEqual(
            'ALTER TABLE `users` ADD `foo` SMALLINT NOT NULL AUTO_INCREMENT PRIMARY KEY',
            statements[0]
        )

    def test_adding_float(self):
        blueprint = Blueprint('users')
        blueprint.float('foo', 5, 2)
        statements = blueprint.to_sql(self.get_connection(), self.get_grammar())

        self.assertEqual(1, len(statements))
        self.assertEqual(
            'ALTER TABLE `users` ADD `foo` DOUBLE(5, 2) NOT NULL',
            statements[0]
        )

    def test_adding_double(self):
        blueprint = Blueprint('users')
        blueprint.double('foo')
        statements = blueprint.to_sql(self.get_connection(), self.get_grammar())

        self.assertEqual(1, len(statements))
        self.assertEqual(
            'ALTER TABLE `users` ADD `foo` DOUBLE NOT NULL',
            statements[0]
        )

    def test_adding_double_with_precision(self):
        blueprint = Blueprint('users')
        blueprint.double('foo', 15, 8)
        statements = blueprint.to_sql(self.get_connection(), self.get_grammar())

        self.assertEqual(1, len(statements))
        self.assertEqual(
            'ALTER TABLE `users` ADD `foo` DOUBLE(15, 8) NOT NULL',
            statements[0]
        )

    def test_adding_decimal(self):
        blueprint = Blueprint('users')
        blueprint.decimal('foo', 5, 2)
        statements = blueprint.to_sql(self.get_connection(), self.get_grammar())

        self.assertEqual(1, len(statements))
        self.assertEqual(
            'ALTER TABLE `users` ADD `foo` DECIMAL(5, 2) NOT NULL',
            statements[0]
        )

    def test_adding_boolean(self):
        blueprint = Blueprint('users')
        blueprint.boolean('foo')
        statements = blueprint.to_sql(self.get_connection(), self.get_grammar())

        self.assertEqual(1, len(statements))
        self.assertEqual(
            'ALTER TABLE `users` ADD `foo` TINYINT(1) NOT NULL',
            statements[0]
        )

    def test_adding_enum(self):
        blueprint = Blueprint('users')
        blueprint.enum('foo', ['bar', 'baz'])
        statements = blueprint.to_sql(self.get_connection(), self.get_grammar())

        self.assertEqual(1, len(statements))
        self.assertEqual(
            'ALTER TABLE `users` ADD `foo` ENUM(\'bar\', \'baz\') NOT NULL',
            statements[0]
        )

    def test_adding_date(self):
        blueprint = Blueprint('users')
        blueprint.date('foo')
        statements = blueprint.to_sql(self.get_connection(), self.get_grammar())

        self.assertEqual(1, len(statements))
        self.assertEqual(
            'ALTER TABLE `users` ADD `foo` DATE NOT NULL',
            statements[0]
        )

    def test_adding_datetime(self):
        blueprint = Blueprint('users')
        blueprint.datetime('foo')
        statements = blueprint.to_sql(self.get_connection(), self.get_grammar())

        self.assertEqual(1, len(statements))
        self.assertEqual(
            'ALTER TABLE `users` ADD `foo` DATETIME NOT NULL',
            statements[0]
        )

    def test_adding_time(self):
        blueprint = Blueprint('users')
        blueprint.time('foo')
        statements = blueprint.to_sql(self.get_connection(), self.get_grammar())

        self.assertEqual(1, len(statements))
        self.assertEqual(
            'ALTER TABLE `users` ADD `foo` TIME NOT NULL',
            statements[0]
        )

    def test_adding_timestamp(self):
        blueprint = Blueprint('users')
        blueprint.timestamp('foo')
        statements = blueprint.to_sql(self.get_connection(), self.get_grammar())

        self.assertEqual(1, len(statements))
        self.assertEqual(
            'ALTER TABLE `users` ADD `foo` TIMESTAMP DEFAULT 0 NOT NULL',
            statements[0]
        )

    def test_adding_timestamps(self):
        blueprint = Blueprint('users')
        blueprint.timestamps()
        statements = blueprint.to_sql(self.get_connection(), self.get_grammar())

        self.assertEqual(1, len(statements))
        expected = [
            'ALTER TABLE `users` ADD `created_at` TIMESTAMP DEFAULT 0 NOT NULL, '
            'ADD `updated_at` TIMESTAMP DEFAULT 0 NOT NULL'
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
            'ALTER TABLE `users` ADD `foo` BLOB NOT NULL',
            statements[0]
        )

    def get_connection(self):
        return flexmock(Connection(None))

    def get_grammar(self):
        return MySqlSchemaGrammar()
