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
        # The code is a little complex. It will propably change
        # if we support complete diffs in dbal
        sql = []

        schema = connection.get_schema_manager()
        table = self.get_table_prefix() + blueprint.get_table()

        column = connection.get_column(table, command.from_)

        columns = schema.list_table_columns(table).values()
        indexes = schema.list_table_indexes(table)
        foreign_keys = schema.list_table_foreign_keys(table)

        diff = self._get_renamed_diff(blueprint, command, column, schema)
        renamed_columns = diff.renamed_columns

        old_column_names = list(map(lambda x: x.get_name(), columns))

        # We build the new column names
        new_column_names = []
        for column_name in old_column_names:
            if column_name in renamed_columns:
                new_column_names.append(renamed_columns[column_name].get_name())
            else:
                new_column_names.append(column_name)

        # We create a temporary table and insert the data into it
        temp_table = '__temp__' + self.get_table_prefix() + blueprint.get_table()
        sql.append('CREATE TEMPORARY TABLE %s AS SELECT %s FROM %s'
                   % (temp_table, self.columnize(old_column_names), table))

        # We drop the current table
        sql += Blueprint(table).drop().to_sql(None, self)

        # Building the list a new columns
        new_columns = []
        for column in columns:
            for column_name, changed_column in renamed_columns.items():
                if column_name == column.get_name():
                    new_columns.append(changed_column)

        # Here we will try to rebuild a new blueprint to create a new table
        # with the original name
        new_blueprint = Blueprint(table)
        new_blueprint.create()
        primary = []
        for column in columns:
            # Mapping the database type to the blueprint type
            type = column.get_type()
            if type == 'smallint':
                type = 'small_integer'
            elif type == 'bigint':
                type = 'big_integer'
            elif type == 'blob':
                type = 'binary'

            # If the column is a primary, we will add it to the blueprint later
            if column.get_platform_option('pk'):
                primary.append(column.get_name())

            # If the column is not one that's been renamed we reinsert it into the blueprint
            if column.get_name() not in renamed_columns.keys():
                col = getattr(new_blueprint, type)(column.get_name())

                # If the column is nullable, we flag it
                if not column.get_notnull():
                    col.nullable()

                # If the column has a default value, we add it
                if column.get_default() is not None:
                    col.default(QueryExpression(column.get_default()))

        # Inserting the renamed columns into the blueprint
        for column in new_columns:
            type = column.get_type()
            if type == 'smallint':
                type = 'small_integer'
            elif type == 'bigint':
                type = 'big_integer'
            elif type == 'blob':
                type = 'binary'

            col = getattr(new_blueprint, type)(column.get_name())
            if not column.get_notnull():
                col.nullable()

            if column.get_default() is not None:
                col.default(QueryExpression(column.get_default()))

        # We add the primary keys
        if primary:
            new_blueprint.primary(primary)

        # We rebuild the indexes
        for index in indexes:
            index_columns = index['columns']
            new_index_columns = []
            index_name = index['name']

            for column_name in index_columns:
                if column_name in renamed_columns:
                    new_index_columns.append(renamed_columns[column_name].get_name())
                else:
                    new_index_columns.append(column_name)

            if index_columns != new_index_columns:
                index_name = None

            if index['unique']:
                new_blueprint.unique(new_index_columns, index_name)
            else:
                new_blueprint.index(index['columns'], index_name)

        for foreign_key in foreign_keys:
            fkey_from = foreign_key['from']
            if fkey_from in renamed_columns:
                fkey_from = renamed_columns[fkey_from].get_name()

            new_blueprint.foreign(fkey_from)\
                .references(foreign_key['to'])\
                .on(foreign_key['table'])\
                .on_delete(foreign_key['on_delete'])\
                .on_update(foreign_key['on_update'])

        # We create the table
        sql += new_blueprint.to_sql(None, self)

        # We reinsert the data into the new table
        sql.append('INSERT INTO %s (%s) SELECT %s FROM %s'
                   % (self.wrap_table(table),
                      ', '.join(new_column_names),
                      self.columnize(old_column_names),
                      self.wrap_table(temp_table)
                      ))

        # Finally we drop the temporary table
        sql += Blueprint(temp_table).drop().to_sql(None, self)

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

        schema = connection.get_schema_manager()
        table = self.get_table_prefix() + blueprint.get_table()

        columns = schema.list_table_columns(table).values()
        indexes = schema.list_table_indexes(table)
        foreign_keys = schema.list_table_foreign_keys(table)

        diff = self._get_changed_diff(blueprint, schema)
        blueprint_changed_columns = blueprint.get_changed_columns()
        changed_columns = diff.changed_columns

        temp_table = '__temp__' + self.get_table_prefix() + blueprint.get_table()
        sql.append('CREATE TEMPORARY TABLE %s AS SELECT %s FROM %s'
                   % (temp_table, self.columnize(list(map(lambda x: x.get_name(), columns))), table))
        sql += Blueprint(table).drop().to_sql(None, self)

        new_columns = []
        for column in columns:
            for column_name, changed_column in changed_columns.items():
                if column_name == column.get_name():
                    for blueprint_column in blueprint_changed_columns:
                        if blueprint_column.name == column_name:
                            new_columns.append(blueprint_column)
                            break

                    break

        new_blueprint = Blueprint(table)
        new_blueprint.create()
        primary = []
        new_column_names = []
        for column in columns:
            type = column.get_type()
            if type == 'smallint':
                type = 'small_integer'
            elif type == 'bigint':
                type = 'big_integer'
            elif type == 'blob':
                type = 'binary'

            if column.get_platform_option('pk'):
                primary.append(column.get_name())

            if column.get_name() not in changed_columns:
                col = getattr(new_blueprint, type)(column.get_name())
                if not column.get_notnull():
                    col.nullable()

                new_column_names.append(column.get_name())

        for column in new_columns:
            column.change = False
            new_blueprint._add_column(**column.get_attributes())
            new_column_names.append(column.name)

        if primary:
            new_blueprint.primary(primary)

        for index in indexes:
            if index['unique']:
                new_blueprint.unique(index['columns'], index['name'])
            else:
                new_blueprint.index(index['columns'], index['name'])

        for foreign_key in foreign_keys:
            new_blueprint.foreign(foreign_key['from'])\
                .references(foreign_key['to'])\
                .on(foreign_key['table'])\
                .on_delete(foreign_key['on_delete'])\
                .on_update(foreign_key['on_update'])

        sql += new_blueprint.to_sql(None, self)
        sql.append('INSERT INTO %s (%s) SELECT %s FROM %s'
                   % (self.wrap_table(table),
                      ', '.join(sorted(new_column_names)),
                      self.columnize(sorted(list(map(lambda x: x.get_name(), columns)))),
                      self.wrap_table(temp_table)
                      ))
        sql += Blueprint(temp_table).drop().to_sql(None, self)

        return sql

    def compile_table_exists(self):
        """
        Compile the query to determine if a table exists

        :rtype: str
        """
        return "SELECT * FROM sqlite_master WHERE type = 'table' AND name = ?"

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
        # The code is a little complex. It will propably change
        # if we support complete diffs in dbal
        sql = []

        schema = connection.get_schema_manager()
        table = self.get_table_prefix() + blueprint.get_table()

        columns = schema.list_table_columns(table).values()
        indexes = schema.list_table_indexes(table)
        foreign_keys = schema.list_table_foreign_keys(table)

        diff = self._get_table_diff(blueprint, schema)

        for name in command.columns:
            column = connection.get_column(blueprint.get_table(), name)

            diff.removed_columns[name] = column

        removed_columns = diff.removed_columns

        old_column_names = list(map(lambda x: x.get_name(), columns))

        # We build the new column names
        new_column_names = []
        for column_name in old_column_names:
            if column_name not in removed_columns:
                new_column_names.append(column_name)

        # We create a temporary table and insert the data into it
        temp_table = '__temp__' + self.get_table_prefix() + blueprint.get_table()
        sql.append('CREATE TEMPORARY TABLE %s AS SELECT %s FROM %s'
                   % (temp_table, self.columnize(old_column_names), table))

        # We drop the current table
        sql += Blueprint(table).drop().to_sql(None, self)

        # Here we will try to rebuild a new blueprint to create a new table
        # with the original name
        new_blueprint = Blueprint(table)
        new_blueprint.create()
        primary = []
        for column in columns:
            # If the column is not one that's been removed we reinsert it into the blueprint
            if column.get_name() in new_column_names:
                # Mapping the database type to the blueprint type
                type = column.get_type()
                if type == 'smallint':
                    type = 'small_integer'
                elif type == 'bigint':
                    type = 'big_integer'
                elif type == 'blob':
                    type = 'binary'

                # If the column is a primary, we will add it to the blueprint later
                if column.get_platform_option('pk'):
                    primary.append(column.get_name())

                col = getattr(new_blueprint, type)(column.get_name())

                # If the column is nullable, we flag it
                if not column.get_notnull():
                    col.nullable()

                # If the column has a default value, we add it
                if column.get_default() is not None:
                    col.default(QueryExpression(column.get_default()))

        # We add the primary keys
        if primary:
            new_blueprint.primary(primary)

        # We rebuild the indexes
        for index in indexes:
            index_columns = index['columns']
            new_index_columns = []
            index_name = index['name']

            removed = False
            for column_name in index_columns:
                if column_name not in removed_columns:
                    new_index_columns.append(column_name)
                else:
                    removed = True
                    break

            if removed:
                continue

            if index_columns != new_index_columns:
                index_name = None

            if index['unique']:
                new_blueprint.unique(new_index_columns, index_name)
            else:
                new_blueprint.index(index['columns'], index_name)

        for foreign_key in foreign_keys:
            fkey_from = foreign_key['from']
            if fkey_from in removed_columns:
                continue

            new_blueprint.foreign(fkey_from)\
                .references(foreign_key['to'])\
                .on(foreign_key['table'])\
                .on_delete(foreign_key['on_delete'])\
                .on_update(foreign_key['on_update'])

        # We create the table
        sql += new_blueprint.to_sql(None, self)

        # We reinsert the data into the new table
        sql.append('INSERT INTO %s (%s) SELECT %s FROM %s'
                   % (self.wrap_table(table),
                      self.columnize(new_column_names),
                      self.columnize(new_column_names),
                      self.wrap_table(temp_table)
                      ))

        # Finally we drop the temporary table
        sql += Blueprint(temp_table).drop().to_sql(None, self)

        return sql

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
