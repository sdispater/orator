# -*- coding: utf-8 -*-

import re
from .column import Column
from .foreign_key_constraint import ForeignKeyConstraint
from .schema_manager import SchemaManager


class PostgresSchemaManager(SchemaManager):

    def _get_portable_table_column_definition(self, table_column):
        if table_column['type'].lower() == 'varchar' or table_column['type'] == 'bpchar':
            length = re.sub('.*\(([0-9]*)\).*', '\\1', table_column['complete_type'])
            table_column['length'] = length

        autoincrement = False
        match = re.match("^nextval\('?(.*)'?(::.*)?\)$", str(table_column['default']))
        if match:
            table_column['sequence'] = match.group(1)
            table_column['default'] = None
            autoincrement = True

        match = re.match("^'?([^']*)'?::.*$", str(table_column['default']))
        if match:
            table_column['default'] = match.group(1)

        if str(table_column['default']).find('NULL') == 0:
            table_column['default'] = None

        if 'length' in table_column:
            length = table_column['length']
        else:
            length = None

        if length == '-1' and 'atttypmod' in table_column:
            length = table_column['atttypmod'] - 4

        if length is None or not length.isdigit() or int(length) <= 0:
            length = None

        fixed = None

        if 'name' not in table_column:
            table_column['name'] = ''

        precision = None
        scale = None

        db_type = table_column['type'].lower()

        type = self._platform.get_type_mapping(db_type)

        if db_type in ['smallint', 'int2']:
            length = None
        elif db_type in ['int', 'int4', 'integer']:
            length = None
        elif db_type in ['int8', 'bigint']:
            length = None
        elif db_type in ['bool', 'boolean']:
            if table_column['default'] == 'true':
                table_column['default'] = True

            if table_column['default'] == 'false':
                table_column['default'] = False

            length = None
        elif db_type == 'text':
            fixed = False
        elif db_type in ['varchar', 'interval', '_varchar']:
            fixed = False
        elif db_type in ['char', 'bpchar']:
            fixed = True
        elif db_type in ['float', 'float4', 'float8',
                         'double', 'double precision',
                         'real', 'decimal', 'money', 'numeric']:
            match = re.match('([A-Za-z]+\(([0-9]+),([0-9]+)\))', table_column['complete_type'])
            if match:
                precision = match.group(1)
                scale = match.group(2)
                length = None
        elif db_type == 'year':
            length = None

        if table_column['default']:
            match = re.match("('?([^']+)'?::)", str(table_column['default']))
            if match:
                table_column['default'] = match.group(1)

        options = {
            'length': length,
            'notnull': table_column['isnotnull'],
            'default': table_column['default'],
            'primary': table_column['pri'] == 't',
            'precision': precision,
            'scale': scale,
            'fixed': fixed,
            'unsigned': False,
            'autoincrement': autoincrement
        }

        column = Column(table_column['field'], type, options)

        return column

    def _get_portable_table_indexes_list(self, table_indexes, table_name):
        buffer = []

        for row in table_indexes:
            col_numbers = row['indkey'].split(' ')
            col_numbers_sql = 'IN (%s)' % ', '.join(col_numbers)
            column_name_sql = 'SELECT attnum, attname FROM pg_attribute ' \
                              'WHERE attrelid=%s AND attnum %s ORDER BY attnum ASC;'\
                              % (row['indrelid'], col_numbers_sql)

            index_columns = self._connection.select(column_name_sql)

            # required for getting the order of the columns right.
            for col_num in col_numbers:
                for col_row in index_columns:
                    if int(col_num) == col_row['attnum']:
                        buffer.append({
                            'key_name': row['relname'],
                            'column_name': col_row['attname'].strip(),
                            'non_unique': not row['indisunique'],
                            'primary': row['indisprimary'],
                            'where': row['where']
                        })

        return super(PostgresSchemaManager, self)._get_portable_table_indexes_list(buffer, table_name)

    def _get_portable_table_foreign_key_definition(self, table_foreign_key):
        on_update = ''
        on_delete = ''

        match = re.match('ON UPDATE ([a-zA-Z0-9]+( (NULL|ACTION|DEFAULT))?)', table_foreign_key['condef'])
        if match:
            on_update = match.group(1)

        match = re.match('ON DELETE ([a-zA-Z0-9]+( (NULL|ACTION|DEFAULT))?)', table_foreign_key['condef'])
        if match:
            on_delete = match.group(1)

        values = re.match('FOREIGN KEY \((.+)\) REFERENCES (.+)\((.+)\)', table_foreign_key['condef'])
        if values:
            local_columns = [c.strip() for c in values.group(1).split(',')]
            foreign_columns = [c.strip() for c in values.group(3).split(',')]
            foreign_table = values.group(2)

            return ForeignKeyConstraint(
                local_columns, foreign_table, foreign_columns,
                table_foreign_key['conname'],
                {'on_update': on_update, 'on_delete': on_delete}
            )
