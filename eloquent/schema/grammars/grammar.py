# -*- coding: utf-8 -*-

from ...support.grammar import Grammar
from ...support.fluent import Fluent
from ...query.expression import QueryExpression
from ..blueprint import Blueprint


class SchemaGrammar(Grammar):

    def compile_rename_column(self, blueprint, command, connection):
        """
        Compile a rename column command.

        :param blueprint: The blueprint
        :type blueprint: Blueprint

        :param command: The command
        :type command: Fluent

        :param connection: The connection
        :type connection: eloquent.connections.Connection

        :rtype: list
        """

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

        on_columns = self.columnize(command.references)

        sql = 'ALTER TABLE %s ADD CONSTRAINT %s' % (table, command.index)

        sql += 'FOREIGN KEY (%s) REFERENCES %s (%s)' % (columns, on, on_columns)

        if getattr(command, 'on_delete', None):
            sql += ' ON DELETE %s' % command.on_delete

        if getattr(command, 'on_update', None):
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
