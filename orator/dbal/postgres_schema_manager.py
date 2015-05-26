# -*- coding: utf-8 -*-

import re
from .table import Table
from .column import Column
from .schema_manager import SchemaManager
from .platforms.postgres_platform import PostgresPlatform


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

    def get_database_platform(self):
        return PostgresPlatform()
