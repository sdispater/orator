# -*- coding: utf-8 -*-

from .grammar import SchemaGrammar
from ..blueprint import Blueprint
from ...query.expression import QueryExpression
from ...support.fluent import Fluent


class MySQLSchemaGrammar(SchemaGrammar):

    _modifiers = [
        'unsigned', 'charset', 'collate', 'nullable',
        'default', 'increment', 'comment', 'after'
    ]

    _serials = ['big_integer', 'integer',
                'medium_integer', 'small_integer', 'tiny_integer']

    marker = '%s'

    def compile_table_exists(self):
        """
        Compile the query to determine if a table exists

        :rtype: str
        """
        return 'SELECT * ' \
               'FROM information_schema.tables ' \
               'WHERE table_schema = %(marker)s ' \
               'AND table_name = %(marker)s' % {'marker': self.get_marker()}

    def compile_column_exists(self):
        """
        Compile the query to determine the list of columns.
        """
        return 'SELECT column_name ' \
               'FROM information_schema.columns ' \
               'WHERE table_schema = %(marker)s AND table_name = %(marker)s' \
               % {'marker': self.get_marker()}

    def compile_create(self, blueprint, command, connection):
        """
        Compile a create table command.
        """
        columns = ', '.join(self._get_columns(blueprint))

        sql = 'CREATE TABLE %s (%s)' % (self.wrap_table(blueprint), columns)

        sql = self._compile_create_encoding(sql, connection, blueprint)

        if blueprint.engine:
            sql += ' ENGINE = %s' % blueprint.engine

        return sql

    def _compile_create_encoding(self, sql, connection, blueprint):
        """
        Append the character set specifications to a command.

        :type sql: str
        :type connection: orator.connections.Connection
        :type blueprint: Blueprint

        :rtype: str
        """
        charset = blueprint.charset or connection.get_config('charset')
        if charset:
            sql += ' DEFAULT CHARACTER SET %s' % charset

        collation = blueprint.collation or connection.get_config('collation')
        if collation:
            sql += ' COLLATE %s' % collation

        return sql

    def compile_add(self, blueprint, command, _):
        table = self.wrap_table(blueprint)

        columns = self.prefix_list('ADD', self._get_columns(blueprint))

        return 'ALTER TABLE %s %s' % (table, ', '.join(columns))

    def compile_primary(self, blueprint, command, _):
        command.name = None

        return self._compile_key(blueprint, command, 'PRIMARY KEY')

    def compile_unique(self, blueprint, command, _):
        return self._compile_key(blueprint, command, 'UNIQUE')

    def compile_index(self, blueprint, command, _):
        return self._compile_key(blueprint, command, 'INDEX')

    def _compile_key(self, blueprint, command, type):
        columns = self.columnize(command.columns)

        table = self.wrap_table(blueprint)

        return 'ALTER TABLE %s ADD %s %s(%s)' % (table, type, command.index, columns)

    def compile_drop(self, blueprint, command, _):
        return 'DROP TABLE %s' % self.wrap_table(blueprint)

    def compile_drop_if_exists(self, blueprint, command, _):
        return 'DROP TABLE IF EXISTS %s' % self.wrap_table(blueprint)

    def compile_drop_column(self, blueprint, command, connection):
        columns = self.prefix_list('DROP', self.wrap_list(command.columns))

        table = self.wrap_table(blueprint)

        return 'ALTER TABLE %s %s' % (table, ', '.join(columns))

    def compile_drop_primary(self, blueprint, command, _):
        return 'ALTER TABLE %s DROP PRIMARY KEY'\
               % self.wrap_table(blueprint)

    def compile_drop_unique(self, blueprint, command, _):
        table = self.wrap_table(blueprint)

        return 'ALTER TABLE %s DROP INDEX %s' % (table, command.index)

    def compile_drop_index(self, blueprint, command, _):
        table = self.wrap_table(blueprint)

        return 'ALTER TABLE %s DROP INDEX %s' % (table, command.index)

    def compile_drop_foreign(self, blueprint, command, _):
        table = self.wrap_table(blueprint)

        return 'ALTER TABLE %s DROP FOREIGN KEY %s' % (table, command.index)

    def compile_rename(self, blueprint, command, _):
        from_ = self.wrap_table(blueprint)

        return 'RENAME TABLE %s TO %s' % (from_, self.wrap_table(command.to))

    def _type_char(self, column):
        return "CHAR(%s)" % column.length

    def _type_string(self, column):
        return "VARCHAR(%s)" % column.length

    def _type_text(self, column):
        return 'TEXT'

    def _type_medium_text(self, column):
        return 'MEDIUMTEXT'

    def _type_long_text(self, column):
        return 'LONGTEXT'

    def _type_integer(self, column):
        return 'INT'

    def _type_big_integer(self, column):
        return 'BIGINT'

    def _type_medium_integer(self, column):
        return 'MEDIUMINT'

    def _type_tiny_integer(self, column):
        return 'TINYINT'

    def _type_small_integer(self, column):
        return 'SMALLINT'

    def _type_float(self, column):
        return self._type_double(column)

    def _type_double(self, column):
        if column.total and column.places:
            return 'DOUBLE(%s, %s)' % (column.total, column.places)

        return 'DOUBLE'

    def _type_decimal(self, column):
        return 'DECIMAL(%s, %s)' % (column.total, column.places)

    def _type_boolean(self, column):
        return 'TINYINT(1)'

    def _type_enum(self, column):
        return 'ENUM(\'%s\')' % '\', \''.join(column.allowed)

    def _type_json(self, column):
        if self.platform().has_native_json_type():
            return 'JSON'

        return 'TEXT'

    def _type_date(self, column):
        return 'DATE'

    def _type_datetime(self, column):
        return 'DATETIME'

    def _type_time(self, column):
        return 'TIME'

    def _type_timestamp(self, column):
        if column.use_current:
            if self.platform_version() >= (5, 6):
                return 'TIMESTAMP DEFAULT CURRENT_TIMESTAMP'
            else:
                return 'TIMESTAMP DEFAULT 0'

        return 'TIMESTAMP'

    def _type_binary(self, column):
        return 'BLOB'

    def _modify_unsigned(self, blueprint, column):
        if column.get('unsigned', False):
            return ' UNSIGNED'

        return ''

    def _modify_charset(self, blueprint, column):
        if column.get('charset'):
            return ' CHARACTER SET ' + column.charset

        return ''

    def _modify_collate(self, blueprint, column):
        if column.get('collation'):
            return ' COLLATE ' + column.collation

        return ''

    def _modify_nullable(self, blueprint, column):
        if column.get('nullable'):
            return ' NULL'

        return ' NOT NULL'

    def _modify_default(self, blueprint, column):
        if column.get('default') is not None:
            return ' DEFAULT %s' % self._get_default_value(column.default)

        return ''

    def _modify_increment(self, blueprint, column):
        if column.type in self._serials and column.auto_increment:
            return ' AUTO_INCREMENT PRIMARY KEY'

        return ''

    def _modify_after(self, blueprint, column):
        if column.get('after') is not None:
            return ' AFTER ' + self.wrap(column.after)

        return ''

    def _modify_comment(self, blueprint, column):
        if column.get('comment') is not None:
            return ' COMMENT "%s"' % column.comment

        return ''

    def _get_column_change_options(self, fluent):
        """
        Get the column change options.
        """
        options = super(MySQLSchemaGrammar, self)._get_column_change_options(fluent)

        if fluent.type == 'enum':
            options['extra'] = {
                'definition': '(\'{}\')'.format('\',\''.join(fluent.allowed))
            }

        return options

    def _wrap_value(self, value):
        if value == '*':
            return value

        return '`%s`' % value.replace('`', '``')
