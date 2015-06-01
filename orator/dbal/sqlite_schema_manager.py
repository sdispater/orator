# -*- coding: utf-8 -*-

import re
from .schema_manager import SchemaManager
from .platforms.sqlite_platform import SQLitePlatform
from .column import Column


class SQLiteSchemaManager(SchemaManager):

    def _get_portable_table_column_definition(self, table_column):
        parts = table_column['type'].split('(')
        table_column['type'] = parts[0]
        if len(parts) > 1:
            length = parts[1].strip(')')
            table_column['length'] = length

        db_type = table_column['type'].lower()
        length = table_column.get('length', None)
        unsigned = False

        if ' unsigned' in db_type:
            db_type = db_type.replace(' unsigned', '')
            unsigned = True

        fixed = False

        type = self._platform.get_type_mapping(db_type)
        default = table_column['dflt_value']
        if default == 'NULL':
            default = None

        if default is not None:
            # SQLite returns strings wrapped in single quotes, so we need to strip them
            default = re.sub("^'(.*)'$", '\\1', default)

        notnull = bool(table_column['notnull'])

        if 'name' not in table_column:
            table_column['name'] = ''

        precision = None
        scale = None

        if db_type in ['char']:
            fixed = True
        elif db_type in ['float', 'double', 'real', 'decimal', 'numeric']:
            if 'length' in table_column:
                if ',' not in table_column['length']:
                    table_column['length'] += ',0'

                precision, scale = tuple(map(lambda x: x.strip(), table_column['length'].split(',')))

            length = None

        options = {
            'length': length,
            'unsigned': bool(unsigned),
            'fixed': fixed,
            'notnull': notnull,
            'default': default,
            'precision': precision,
            'scale': scale,
            'autoincrement': False
        }

        column = Column(table_column['name'], type, options)
        column.set_platform_option('pk', table_column['pk'])

        return column

    def list_table_indexes(self, table):
        sql = self._platform.get_list_table_indexes_sql(table)

        cursor = self._connection.get_connection().cursor()
        table_indexes = cursor.execute(sql).fetchall()

        indexes = []
        for index in table_indexes:
            table_index = dict(index.items())
            index_info = cursor.execute('PRAGMA index_info(%s)' % index['name']).fetchall()
            columns = []
            for column in index_info:
                columns.append(column['name'])

            table_index['columns'] = columns

            indexes.append(table_index)

        return indexes

    def get_database_platform(self):
        return SQLitePlatform()
