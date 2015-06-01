# -*- coding: utf-8 -*-

from .platform import Platform
from ..table import Table
from ..column import Column


class SQLitePlatform(Platform):

    INTERNAL_TYPE_MAPPING = {
        'boolean': 'boolean',
        'tinyint': 'boolean',
        'smallint': 'smallint',
        'mediumint': 'integer',
        'int': 'integer',
        'integer': 'integer',
        'serial': 'integer',
        'bigint': 'bigint',
        'bigserial': 'bigint',
        'clob': 'text',
        'tinytext': 'text',
        'mediumtext': 'text',
        'longtext': 'text',
        'text': 'text',
        'varchar': 'string',
        'longvarchar': 'string',
        'varchar2': 'string',
        'nvarchar': 'string',
        'image': 'string',
        'ntext': 'string',
        'char': 'string',
        'date': 'date',
        'datetime': 'datetime',
        'timestamp': 'datetime',
        'time': 'time',
        'float': 'float',
        'double': 'float',
        'double precision': 'float',
        'real': 'float',
        'decimal': 'decimal',
        'numeric': 'decimal',
        'blob': 'blob'
    }

    def get_list_table_columns_sql(self, table):
        table = table.replace('.', '__')

        return 'PRAGMA table_info(\'%s\')' % table

    def get_list_table_indexes_sql(self, table):
        table = table.replace('.', '__')

        return 'PRAGMA index_list(\'%s\')' % table

    def get_list_table_foreign_keys_sql(self, table):
        table = table.replace('.', '__')

        return 'PRAGMA foreign_key_list(\'%s\')' % table

    def get_alter_table_sql(self, diff):
        """
        Get the ALTER TABLE SQL statement

        :param diff: The table diff
        :type diff: orator.dbal.table_diff.TableDiff

        :rtype: list
        """
        #sql = self._get_simple_alter_table_sql(diff)

        from_table = diff.from_table
        if not isinstance(from_table, Table):
            raise Exception('SQLite platform requires for the alter table the table diff '
                            'referencing the original table')

        table = from_table.clone()
        columns = {}
        old_column_names = {}
        new_column_names = {}
        column_sql = []
        for column_name, column in table.get_columns().items():
            column_name = column_name.lower()
            columns[column_name] = column
            old_column_names[column_name] = column.get_name()
            new_column_names[column_name] = column.get_name()

        for column_name, column in diff.removed_columns.items():
            column_name = column_name.lower()
            if column_name in columns:
                del columns[column_name]
                del old_column_names[column_name]
                del new_column_names[column_name]

        for old_column_name, column in diff.renamed_columns.items():
            old_column_name = old_column_name.lower()
            if old_column_name in columns:
                del columns[old_column_name]

            columns[column.get_name().lower()] = column

            if old_column_name in new_column_names:
                new_column_names[old_column_name] = column.get_name()

        for old_column_name, column_diff in diff.changed_columns.items():
            if old_column_name in columns:
                del columns[old_column_name]

            columns[column_diff.column.get_name().lower()] = column_diff.column

            if old_column_name in new_column_names:
                new_column_names[old_column_name] = column_diff.column.get_name()

        for column_name, column in diff.added_columns.items():
            columns[column_name.lower()] = column

        sql = []
        table_sql = []

        data_table = Table('__temp__' + table.get_name())

        new_table = Table(table.get_name(), columns,
                          self.get_primary_index_in_altered_table(diff),
                          self.get_foreign_keys_in_altered_table(diff))
        new_table.add_option('alter', True)

        sql = self.get_pre_alter_table_index_foreign_key_sql(diff)
        sql.append('CREATE TEMPORARY TABLE %s AS SELECT %s FROM %s'
                   % (data_table.get_name(), ', '.join(old_column_names.values()), table.get_name()))
        sql.append(self.get_drop_table_sql(from_table))

        sql += self.get_create_table_sql(new_table)
        sql.append('INSERT INTO %s (%s) SELECT %s FROM %s'
                   % (new_table.get_name(),
                      ', '.join(new_column_names.values()),
                      ', '.join(old_column_names.values()),
                      data_table.get_name()))
        sql.append(self.get_drop_table_sql(data_table))

        #sql += self.get_post_alter_table_index_foreign_key_sql(diff)

        return sql

    def _get_simple_alter_table_sql(self, diff):
        for old_column_name, column_diff in diff.changed_columns.items():
            if not isinstance(column_diff.from_column, Column)\
                    or not isinstance(column_diff.column, Column)\
                    or not column_diff.column.get_autoincrement()\
                    or column_diff.column.get_type().lower() != 'integer':
                continue

            if not column_diff.has_changed('type') and not column_diff.has_changed('unsigned'):
                del diff.changed_columns[old_column_name]

                continue

            from_column_type = column_diff.column.get_type()

            if from_column_type == 'smallint' or from_column_type == 'bigint':
                del diff.changed_columns[old_column_name]

        if any([not diff.renamed_columns, not diff.added_foreign_keys, not diff.added_indexes,
                not diff.changed_columns, not diff.changed_foreign_keys, not diff.changed_indexes,
                not diff.removed_columns, not diff.removed_foreign_keys, not diff.removed_indexes,
                not diff.renamed_indexes]):
            return False

        table = Table(diff.name)

        sql = []
        table_sql = []
        column_sql = []

        for column in diff.added_columns.values():
            field = {
                'unique': None,
                'autoincrement': None,
                'default': None
            }
            field.update(column.to_dict())

    def get_foreign_keys_in_altered_table(self, diff):
        """
        :param diff: The table diff
        :type diff: orator.dbal.table_diff.TableDiff

        :rtype: list
        """
        foreign_keys = diff.from_table.get_foreign_keys()
        column_names = self.get_column_names_in_altered_table(diff)

        for key, constraint in foreign_keys.items():
            changed = False
            local_columns = []
            for column_name in constraint.get_local_columns():
                normalized_column_name = column_name.lower()
                if normalized_column_name not in column_names:
                    del foreign_keys[key]
                    break
                else:
                    local_columns.append(column_names[normalized_column_name])
                    if column_name != column_names[normalized_column_name]:
                        changed = True

            if changed:
                pass

        return foreign_keys

    def supports_foreign_key_constraints(self):
        return False

    def get_boolean_type_declaration_sql(self, column):
        return 'BOOLEAN'

    def get_integer_type_declaration_sql(self, column):
        return 'INTEGER' + self._get_common_integer_type_declaration_sql(column)

    def get_bigint_type_declaration_sql(self, column):
        # SQLite autoincrement is implicit for INTEGER PKs, but not for BIGINT fields.
        if not column.get('autoincrement', False):
            return self.get_integer_type_declaration_sql(column)

        return 'BIGINT' + self._get_common_integer_type_declaration_sql(column)

    def get_tinyint_type_declaration_sql(self, column):
        # SQLite autoincrement is implicit for INTEGER PKs, but not for TINYINT fields.
        if not column.get('autoincrement', False):
            return self.get_integer_type_declaration_sql(column)

        return 'TINYINT' + self._get_common_integer_type_declaration_sql(column)

    def get_smallint_type_declaration_sql(self, column):
        # SQLite autoincrement is implicit for INTEGER PKs, but not for SMALLINT fields.
        if not column.get('autoincrement', False):
            return self.get_integer_type_declaration_sql(column)

        return 'SMALLINT' + self._get_common_integer_type_declaration_sql(column)

    def get_mediumint_type_declaration_sql(self, column):
        # SQLite autoincrement is implicit for INTEGER PKs, but not for MEDIUMINT fields.
        if not column.get('autoincrement', False):
            return self.get_integer_type_declaration_sql(column)

        return 'MEDIUMINT' + self._get_common_integer_type_declaration_sql(column)

    def get_datetime_type_declaration_sql(self, column):
        return 'DATETIME'

    def get_date_type_declaration_sql(self, column):
        return 'DATE'

    def get_time_type_declaration_sql(self, column):
        return 'TIME'

    def _get_common_integer_type_declaration_sql(self, column):
        # sqlite autoincrement is implicit for integer PKs, but not when the field is unsigned
        if not column.get('autoincrement', False):
            return ''

        if not column.get('unsigned', False):
            return ' UNSIGNED'

        return ''

    def get_varchar_type_declaration_sql_snippet(self, length, fixed):
        if fixed:
            return 'CHAR(%s)' % length if length else 'CHAR(255)'
        else:
            return 'VARCHAR(%s)' % length if length else 'TEXT'

    def get_blob_type_sql_declaration(self, column):
        return 'BLOB'

    def get_column_options(self):
        return ['pk']
