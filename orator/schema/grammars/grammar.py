# -*- coding: utf-8 -*-

from ...support.grammar import Grammar
from ...support.fluent import Fluent
from ...query.expression import QueryExpression
from ...dbal.column import Column
from ...dbal.table_diff import TableDiff
from ...dbal.comparator import Comparator
from ..blueprint import Blueprint


class SchemaGrammar(Grammar):

    def __init__(self, connection):
        super(SchemaGrammar, self).__init__(marker=connection.get_marker())

        self._connection = connection

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
        schema = connection.get_schema_manager()

        table = self.get_table_prefix() + blueprint.get_table()

        column = connection.get_column(table, command.from_)

        table_diff = self._get_renamed_diff(blueprint, command, column, schema)

        return schema.get_database_platform().get_alter_table_sql(table_diff)

    def _get_renamed_diff(self, blueprint, command, column, schema):
        """
        Get a new column instance with the new column name.

        :param blueprint: The blueprint
        :type blueprint: Blueprint

        :param command: The command
        :type command: Fluent

        :param column: The column
        :type column: orator.dbal.Column

        :param schema: The schema
        :type schema: orator.dbal.SchemaManager

        :rtype: orator.dbal.TableDiff
        """
        table_diff = self._get_table_diff(blueprint, schema)

        return self._set_renamed_columns(table_diff, command, column)

    def _set_renamed_columns(self, table_diff, command, column):
        """
        Set the renamed columns on the table diff.

        :rtype: orator.dbal.TableDiff
        """
        new_column = Column(command.to, column.get_type(), column.to_dict())

        table_diff.renamed_columns = {command.from_: new_column}

        return table_diff

    def compile_foreign(self, blueprint, command, _):
        """
        Compile a foreign key command.

        :param blueprint: The blueprint
        :type blueprint: Blueprint

        :param command: The command
        :type command: Fluent

        :rtype: str
        """
        table = self.wrap_table(blueprint)

        on = self.wrap_table(command.on)

        columns = self.columnize(command.columns)

        on_columns = self.columnize(command.references
                                    if isinstance(command.references, list)
                                    else [command.references])

        sql = 'ALTER TABLE %s ADD CONSTRAINT %s ' % (table, command.index)

        sql += 'FOREIGN KEY (%s) REFERENCES %s (%s)' % (columns, on, on_columns)

        if command.get('on_delete'):
            sql += ' ON DELETE %s' % command.on_delete

        if command.get('on_update'):
            sql += ' ON UPDATE %s' % command.on_update

        return sql

    def _get_columns(self, blueprint):
        """
        Get the blueprint's columns definitions.

        :param blueprint: The blueprint
        :type blueprint: Blueprint

        :rtype: list
        """
        columns = []

        for column in blueprint.get_added_columns():
            sql = self.wrap(column) + ' ' + self._get_type(column)

            columns.append(self._add_modifiers(sql, blueprint, column))

        return columns

    def _add_modifiers(self, sql, blueprint, column):
        """
        Add the column modifiers to the deifinition
        """
        for modifier in self._modifiers:
            method = '_modify_%s' % modifier

            if hasattr(self, method):
                sql += getattr(self, method)(blueprint, column)

        return sql

    def _get_command_by_name(self, blueprint, name):
        """
        Get the primary key command it it exists.
        """
        commands = self._get_commands_by_name(blueprint, name)

        if len(commands):
            return commands[0]

    def _get_commands_by_name(self, blueprint, name):
        """
        Get all of the commands with a given name.
        """
        return list(filter(lambda value: value.name == name, blueprint.get_commands()))

    def _get_type(self, column):
        """
        Get the SQL for the column data type.

        :param column: The column
        :type column: Fluent

        :rtype sql
        """
        return getattr(self, '_type_%s' % column.type)(column)

    def prefix_list(self, prefix, values):
        """
        Add a prefix to a list of values.
        """
        return list(map(lambda value: prefix + ' ' + value, values))

    def wrap_table(self, table):
        if isinstance(table, Blueprint):
            table = table.get_table()

        return super(SchemaGrammar, self).wrap_table(table)

    def wrap(self, value, prefix_alias=False):
        if isinstance(value, Fluent):
            value = value.name

        return super(SchemaGrammar, self).wrap(value, prefix_alias)

    def _get_default_value(self, value):
        """
        Format a value so that it can be used in "default" clauses.
        """
        if isinstance(value, QueryExpression):
            return value

        if isinstance(value, bool):
            return "'%s'" % int(value)

        return "'%s'" % value

    def _get_table_diff(self, blueprint, schema):
        table = self.get_table_prefix() + blueprint.get_table()

        table_diff = TableDiff(table)

        table_diff.from_table = schema.list_table_details(table)

        return table_diff

    def compile_change(self, blueprint, command, connection):
        """
        Compile a change column command into a series of SQL statement.

        :param blueprint: The blueprint
        :type blueprint: Blueprint

        :param command: The command
        :type command: Fluent

        :param connection: The connection
        :type connection: orator.connections.Connection

        :rtype: list
        """
        schema = connection.get_schema_manager()

        table_diff = self._get_changed_diff(blueprint, schema)

        if table_diff:
            sql = schema.get_database_platform().get_alter_table_sql(table_diff)

            if isinstance(sql, list):
                return sql

            return [sql]

        return []

    def _get_changed_diff(self, blueprint, schema):
        """
        Get the table diffrence for the given changes.

        :param blueprint: The blueprint
        :type blueprint: Blueprint

        :param schema: The schema
        :type schema: orator.dbal.SchemaManager

        :rtype: orator.dbal.TableDiff
        """
        table = schema.list_table_details(self.get_table_prefix() + blueprint.get_table())

        return Comparator().diff_table(table, self._get_table_with_column_changes(blueprint, table))

    def _get_table_with_column_changes(self, blueprint, table):
        """
        Get a copy of the given table after making the column changes.

        :param blueprint: The blueprint
        :type blueprint: Blueprint

        :type table: orator.dbal.table.Table

        :rtype: orator.dbal.table.Table
        """
        table = table.clone()

        for fluent in blueprint.get_changed_columns():
            column = self._get_column_for_change(table, fluent)

            for key, value in fluent.get_attributes().items():
                option = self._map_fluent_option(key)

                if option is not None:
                    method = 'set_%s' % option

                    if hasattr(column, method):
                        getattr(column, method)(self._map_fluent_value(option, value))

        return table

    def _get_column_for_change(self, table, fluent):
        """
        Get the column instance for a column change.

        :type table: orator.dbal.table.Table

        :rtype: orator.dbal.column.Column
        """
        return table.change_column(
            fluent.name, self._get_column_change_options(fluent)
        ).get_column(fluent.name)

    def _get_column_change_options(self, fluent):
        """
        Get the column change options.
        """
        options = {
            'name': fluent.name,
            'type': self._get_dbal_column_type(fluent.type),
            'default': fluent.get('default')
        }

        if fluent.type in ['string']:
            options['length'] = fluent.length

        return options

    def _get_dbal_column_type(self, type_):
        """
        Get the dbal column type.

        :param type_: The fluent type
        :type type_: str

        :rtype: str
        """
        type_ = type_.lower()

        if type_ == 'big_integer':
            type_ = 'bigint'
        elif type == 'small_integer':
            type_ = 'smallint'
        elif type_ in ['medium_text', 'long_text']:
            type_ = 'text'

        return type_

    def _map_fluent_option(self, attribute):
        if attribute in ['type', 'name']:
            return
        elif attribute == 'nullable':
            return 'notnull'
        elif attribute == 'total':
            return 'precision'
        elif attribute == 'places':
            return 'scale'
        else:
            return

    def _map_fluent_value(self, option, value):
        if option == 'notnull':
            return not value

        return value

    def platform_version(self, parts=2):
        return self._connection.server_version[:parts]

    def platform(self):
        """
        Returns the dbal database platform.

        :rtype: orator.dbal.platforms.platform.Platform
        """
        return self._connection.get_database_platform()
