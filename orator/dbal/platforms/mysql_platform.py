# -*- coding: utf-8 -*-

from .platform import Platform
from ..table import Table
from ..column import Column


class MySqlPlatform(Platform):

    LENGTH_LIMIT_TINYTEXT = 255
    LENGTH_LIMIT_TEXT = 65535
    LENGTH_LIMIT_MEDIUMTEXT = 16777215

    LENGTH_LIMIT_TINYBLOB = 255
    LENGTH_LIMIT_BLOB = 65535
    LENGTH_LIMIT_MEDIUMBLOB = 16777215

    INTERNAL_TYPE_MAPPING = {
        'tinyint': 'boolean',
        'smallint': 'smallint',
        'mediumint': 'integer',
        'int': 'integer',
        'integer': 'integer',
        'bigint': 'bigint',
        'int8': 'bigint',
        'bool': 'boolean',
        'boolean': 'boolean',
        'tinytext': 'text',
        'mediumtext': 'text',
        'longtext': 'text',
        'text': 'text',
        'varchar': 'string',
        'string': 'string',
        'char': 'string',
        'date': 'date',
        'datetime': 'datetime',
        'timestamp': 'datetime',
        'time': 'time',
        'float': 'float',
        'double': 'float',
        'real': 'float',
        'decimal': 'decimal',
        'numeric': 'decimal',
        'year': 'date',
        'longblob': 'blob',
        'blob': 'blob',
        'mediumblob': 'blob',
        'tinyblob': 'blob',
        'binary': 'binary',
        'varbinary': 'binary',
        'set': 'simple_array'
    }

    def get_list_table_columns_sql(self, table, database=None):
        if database:
            database = "'%s'" % database
        else:
            database = 'DATABASE()'

        return 'SELECT COLUMN_NAME AS field, COLUMN_TYPE AS type, IS_NULLABLE AS `null`, ' \
               'COLUMN_KEY AS `key`, COLUMN_DEFAULT AS `default`, EXTRA AS extra, COLUMN_COMMENT AS comment, ' \
               'CHARACTER_SET_NAME AS character_set, COLLATION_NAME AS collation ' \
               'FROM information_schema.COLUMNS WHERE TABLE_SCHEMA = %s AND TABLE_NAME = \'%s\''\
               % (database, table)

    def get_list_table_indexes_sql(self, table, current_database=None):
        return 'SHOW INDEX FROM %s' % table

    def get_list_table_foreign_keys_sql(self, table, database=None):
        sql = ("SELECT DISTINCT k.`CONSTRAINT_NAME` AS `name`, k.`COLUMN_NAME`, k.`REFERENCED_TABLE_NAME`, "
               "k.`REFERENCED_COLUMN_NAME` /*!50116 , c.update_rule, c.delete_rule */ "
               "FROM information_schema.key_column_usage k /*!50116 "
               "INNER JOIN information_schema.referential_constraints c ON "
               "  c.constraint_name = k.constraint_name AND "
               "  c.table_name = '%s' */ WHERE k.table_name = '%s'" % (table, table))

        if database:
            sql += " AND k.table_schema = '%s' /*!50116 AND c.constraint_schema = '%s' */"\
                   % (database, database)

        sql += " AND k.`REFERENCED_COLUMN_NAME` IS NOT NULL"

        return sql

    def get_alter_table_sql(self, diff):
        """
        Get the ALTER TABLE SQL statement

        :param diff: The table diff
        :type diff: orator.dbal.table_diff.TableDiff

        :rtype: list
        """
        column_sql = []
        query_parts = []

        if diff.new_name is not False:
            query_parts.append('RENAME TO %s' % diff.new_name)

        # Added columns?

        # Removed columns?

        for column_diff in diff.changed_columns.values():
            column = column_diff.column
            column_dict = column.to_dict()

            # Don't propagate default value changes for unsupported column types.
            if column_diff.has_changed('default') \
                    and len(column_diff.changed_properties) == 1 \
                    and (column_dict['type'] == 'text' or column_dict['type'] == 'blob'):
                continue

            query_parts.append('CHANGE %s %s'
                               % (column_diff.get_old_column_name(),
                                  self.get_column_declaration_sql(column.get_name(), column_dict)))

        for old_column_name, column in diff.renamed_columns.items():
            column_dict = column.to_dict()
            query_parts.append('CHANGE %s %s'
                               % (self.quote(old_column_name),
                                  self.get_column_declaration_sql(self.quote(column.get_name()), column_dict)))

        sql = []

        if len(query_parts) > 0:
            sql.append('ALTER TABLE %s %s' % (diff.name, ', '.join(query_parts)))

        return sql

    def convert_booleans(self, item):
        if isinstance(item, list):
            for i, value in enumerate(item):
                if isinstance(value, bool):
                    item[i] = str(value).lower()
        elif isinstance(item, bool):
            item = str(item).lower()

        return item

    def get_boolean_type_sql_declaration(self, column):
        return 'TINYINT(1)'

    def get_integer_type_sql_declaration(self, column):
        return 'INT ' + self._get_common_integer_type_declaration_sql(column)

    def get_bigint_type_sql_declaration(self, column):
        return 'BIGINT ' + self._get_common_integer_type_declaration_sql(column)

    def get_smallint_type_sql_declaration(self, column):
        return 'SMALLINT ' + self._get_common_integer_type_declaration_sql(column)

    def get_guid_type_sql_declaration(self, column):
        return 'UUID'

    def get_datetime_type_sql_declaration(self, column):
        if 'version' in column and column['version'] == True:
            return 'TIMESTAMP'

        return 'DATETIME'

    def get_date_type_sql_declaration(self, column):
        return 'DATE'

    def get_time_type_sql_declaration(self, column):
        return 'TIME'

    def get_varchar_type_declaration_sql_snippet(self, length, fixed):
        if fixed:
            return 'CHAR(%s)' % length if length else 'CHAR(255)'
        else:
            return 'VARCHAR(%s)' % length if length else 'VARCHAR(255)'

    def get_binary_type_declaration_sql_snippet(self, length, fixed):
        if fixed:
            return 'BINARY(%s)' % (length or 255)
        else:
            return 'VARBINARY(%s)' % (length or 255)

    def get_text_type_sql_declaration(self, column):
        length = column.get('length')
        if length:
            if length <= self.LENGTH_LIMIT_TINYTEXT:
                return 'TINYTEXT'

            if length <= self.LENGTH_LIMIT_TEXT:
                return 'TEXT'

            if length <= self.LENGTH_LIMIT_MEDIUMTEXT:
                return 'MEDIUMTEXT'

        return 'LONGTEXT'

    def get_blob_type_sql_declaration(self, column):
        length = column.get('length')
        if length:
            if length <= self.LENGTH_LIMIT_TINYBLOB:
                return 'TINYBLOB'

            if length <= self.LENGTH_LIMIT_BLOB:
                return 'BLOB'

            if length <= self.LENGTH_LIMIT_MEDIUMBLOB:
                return 'MEDIUMBLOB'

        return 'LONGBLOB'

    def get_decimal_type_sql_declaration(self, column):
        decl = super(MySqlPlatform, self).get_decimal_type_sql_declaration(column)

        return decl + self.get_unsigned_declaration(column)

    def get_unsigned_declaration(self, column):
        if column.get('unsigned'):
            return ' UNSIGNED'

        return ''

    def _get_common_integer_type_declaration_sql(self, column):
        autoinc = ''
        if column.get('autoincrement'):
            autoinc = ' AUTO_INCREMENT'

        return self.get_unsigned_declaration(column) + autoinc

    def get_float_type_sql_declaration(self, column):
        return 'DOUBLE PRECISION' + self.get_unsigned_declaration(column)

    def supports_foreign_key_constraints(self):
        return True

    def supports_column_collation(self):
        return False

    def quote(self, name):
        return '`%s`' % name.replace('`', '``')
