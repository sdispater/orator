# -*- coding: utf-8 -*-

from .grammar import SchemaGrammar
from ..blueprint import Blueprint
from ...query.expression import QueryExpression
from ...support.fluent import Fluent


class SQLiteSchemaGrammar(SchemaGrammar):

    _modifiers = ['nullable', 'default', 'increment']

    _serials = ['big_integer', 'integer']

    def compile_rename_column(self, blueprint, command, connection):
        """
        Compile a rename column command.

        :param blueprint: The blueprint
        :type blueprint: Blueprint

        :param command: The command
        :type command: Fluent

        :param connection: The connection
        :type connection: orator.connections.Connection

        :rtype: list
        """
        sql = []
        # If foreign keys are on, we disable them
        foreign_keys = self._connection.select('PRAGMA foreign_keys')
        if foreign_keys:
            foreign_keys = bool(foreign_keys[0])
            if foreign_keys:
                sql.append('PRAGMA foreign_keys = OFF')

        sql += super(SQLiteSchemaGrammar, self).compile_rename_column(blueprint, command, connection)

        if foreign_keys:
            sql.append('PRAGMA foreign_keys = ON')

        return sql

    def compile_change(self, blueprint, command, connection):
        """
        Compile a change column command into a series of SQL statement.

        :param blueprint: The blueprint
        :type blueprint: orator.schema.Blueprint

        :param command: The command
        :type command: Fluent

        :param connection: The connection
        :type connection: orator.connections.Connection

        :rtype: list
        """
        sql = []
        # If foreign keys are on, we disable them
        foreign_keys = self._connection.select('PRAGMA foreign_keys')
        if foreign_keys:
            foreign_keys = bool(foreign_keys[0])
            if foreign_keys:
                sql.append('PRAGMA foreign_keys = OFF')

        sql += super(SQLiteSchemaGrammar, self).compile_change(blueprint, command, connection)

        if foreign_keys:
            sql.append('PRAGMA foreign_keys = ON')

        return sql

    def compile_table_exists(self):
        """
        Compile the query to determine if a table exists

        :rtype: str
        """
        return "SELECT * FROM sqlite_master WHERE type = 'table' AND name = %(marker)s" % {'marker': self.get_marker()}

    def compile_column_exists(self, table):
        """
        Compile the query to determine the list of columns.
        """
        return 'PRAGMA table_info(%s)' % table.replace('.', '__')

    def compile_create(self, blueprint, command, _):
        """
        Compile a create table command.
        """
        columns = ', '.join(self._get_columns(blueprint))

        sql = 'CREATE TABLE %s (%s' % (self.wrap_table(blueprint), columns)

        sql += self._add_foreign_keys(blueprint)

        sql += self._add_primary_keys(blueprint)

        return sql + ')'

    def _add_foreign_keys(self, blueprint):
        sql = ''

        foreigns = self._get_commands_by_name(blueprint, 'foreign')

        for foreign in foreigns:
            sql += self._get_foreign_key(foreign)

            if foreign.get('on_delete'):
                sql += ' ON DELETE %s' % foreign.on_delete

            if foreign.get('on_update'):
                sql += ' ON UPDATE %s' % foreign.on_delete

        return sql

    def _get_foreign_key(self, foreign):
        on = self.wrap_table(foreign.on)

        columns = self.columnize(foreign.columns)

        references = foreign.references
        if not isinstance(references, list):
            references = [references]

        on_columns = self.columnize(references)

        return ', FOREIGN KEY(%s) REFERENCES %s(%s)' % (columns, on, on_columns)

    def _add_primary_keys(self, blueprint):
        primary = self._get_command_by_name(blueprint, 'primary')

        if primary:
            columns = self.columnize(primary.columns)

            return ', PRIMARY KEY (%s)' % columns

        return ''

    def compile_add(self, blueprint, command, _):
        table = self.wrap_table(blueprint)

        columns = self.prefix_list('ADD COLUMN', self._get_columns(blueprint))

        statements = []

        for column in columns:
            statements.append('ALTER TABLE %s %s' % (table, column))

        return statements

    def compile_unique(self, blueprint, command, _):
        columns = self.columnize(command.columns)

        table = self.wrap_table(blueprint)

        return 'CREATE UNIQUE INDEX %s ON %s (%s)' % (command.index, table, columns)

    def compile_index(self, blueprint, command, _):
        columns = self.columnize(command.columns)

        table = self.wrap_table(blueprint)

        return 'CREATE INDEX %s ON %s (%s)' % (command.index, table, columns)

    def compile_foreign(self, blueprint, command, _):
        pass

    def compile_drop(self, blueprint, command, _):
        return 'DROP TABLE %s' % self.wrap_table(blueprint)

    def compile_drop_if_exists(self, blueprint, command, _):
        return 'DROP TABLE IF EXISTS %s' % self.wrap_table(blueprint)

    def compile_drop_column(self, blueprint, command, connection):
        schema = connection.get_schema_manager()

        table_diff = self._get_table_diff(blueprint, schema)

        for name in command.columns:
            column = connection.get_column(blueprint.get_table(), name)

            table_diff.removed_columns[name] = column

        return schema.get_database_platform().get_alter_table_sql(table_diff)

    def compile_drop_unique(self, blueprint, command, _):
        return 'DROP INDEX %s' % command.index

    def compile_drop_index(self, blueprint, command, _):
        return 'DROP INDEX %s' % command.index

    def compile_rename(self, blueprint, command, _):
        from_ = self.wrap_table(blueprint)

        return 'ALTER TABLE %s RENAME TO %s' % (from_, self.wrap_table(command.to))

    def _type_char(self, column):
        return 'VARCHAR'

    def _type_string(self, column):
        return 'VARCHAR'

    def _type_text(self, column):
        return 'TEXT'

    def _type_medium_text(self, column):
        return 'TEXT'

    def _type_long_text(self, column):
        return 'TEXT'

    def _type_integer(self, column):
        return 'INTEGER'

    def _type_big_integer(self, column):
        return 'INTEGER'

    def _type_medium_integer(self, column):
        return 'INTEGER'

    def _type_tiny_integer(self, column):
        return 'TINYINT'

    def _type_small_integer(self, column):
        return 'INTEGER'

    def _type_float(self, column):
        return 'FLOAT'

    def _type_double(self, column):
        return 'FLOAT'

    def _type_decimal(self, column):
        return 'NUMERIC'

    def _type_boolean(self, column):
        return 'TINYINT'

    def _type_enum(self, column):
        return 'VARCHAR'

    def _type_json(self, column):
        return 'TEXT'

    def _type_date(self, column):
        return 'DATE'

    def _type_datetime(self, column):
        return 'DATETIME'

    def _type_time(self, column):
        return 'TIME'

    def _type_timestamp(self, column):
        if column.use_current:
            return 'DATETIME DEFAULT CURRENT_TIMESTAMP'

        return 'DATETIME'

    def _type_binary(self, column):
        return 'BLOB'

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
            return ' PRIMARY KEY AUTOINCREMENT'

        return ''

    def _get_dbal_column_type(self, type_):
        """
        Get the dbal column type.

        :param type_: The fluent type
        :type type_: str

        :rtype: str
        """
        type_ = type_.lower()

        if type_ == 'enum':
            return 'string'

        return super(SQLiteSchemaGrammar, self)._get_dbal_column_type(type_)
