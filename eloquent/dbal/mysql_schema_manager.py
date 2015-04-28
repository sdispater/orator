# -*- coding: utf-8 -*-

import re
from .column import Column
from .schema_manager import SchemaManager
from .platforms.mysql_platform import MySqlPlatform


class MySqlSchemaManager(SchemaManager):

    def _get_portable_table_column_definition(self, table_column):
        db_type = table_column['type'].lower()
        match = re.match('(.+)\((.*)\).*', db_type)
        if match:
            db_type = match.group(1)

        if 'length' in table_column:
            length = table_column['length']
        else:
            if match and match.group(2) and ',' not in match.group(2):
                length = int(match.group(2))
            else:
                length = 0

        fixed = None

        if 'name' not in table_column:
            table_column['name'] = ''

        precision = None
        scale = None

        type = self._platform.get_type_mapping(db_type)

        if db_type in ['char', 'binary']:
            fixed = True
        elif db_type in ['float', 'double', 'real', 'decimal', 'numeric']:
            match = re.match('([A-Za-z]+\(([0-9]+),([0-9]+)\))', table_column['type'])
            if match:
                precision = match.group(1)
                scale = match.group(2)
                length = None
        elif db_type == 'tinytext':
            length = MySqlPlatform.LENGTH_LIMIT_TINYTEXT
        elif db_type == 'text':
            length = MySqlPlatform.LENGTH_LIMIT_TEXT
        elif db_type == 'mediumtext':
            length = MySqlPlatform.LENGTH_LIMIT_MEDIUMTEXT
        elif db_type == 'tinyblob':
            length = MySqlPlatform.LENGTH_LIMIT_TINYBLOB
        elif db_type == 'blob':
            length = MySqlPlatform.LENGTH_LIMIT_BLOB
        elif db_type == 'mediumblob':
            length = MySqlPlatform.LENGTH_LIMIT_MEDIUMBLOB
        elif db_type in ['tinyint', 'smallint', 'mediumint', 'int', 'bigint', 'year']:
            length = None

        if length is None or length == 0:
            length = None

        options = {
            'length': length,
            'unsigned': table_column['type'].find('unsigned') != -1,
            'fixed': fixed,
            'notnull': table_column['null'] != 'YES',
            'default': table_column.get('default'),
            'precision': None,
            'scale': None,
            'autoincrement': table_column['extra'].find('auto_increment') != -1
        }

        if scale is not None and precision is not None:
            options['scale'] = scale
            options['precision'] = precision

        column = Column(table_column['field'], type, options)

        if 'collation' in table_column:
            column.set_platform_option('collation', table_column['collation'])

        return column

    def get_database_platform(self):
        return MySqlPlatform()
