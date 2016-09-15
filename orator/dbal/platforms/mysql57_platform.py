# -*- coding: utf-8 -*-

from .mysql_platform import MySQLPlatform


class MySQL57Platform(MySQLPlatform):

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
        'set': 'simple_array',
        'enum': 'enum',
        'json': 'json',
    }

    def get_json_type_declaration_sql(self, column):
        return 'JSON'

    def has_native_json_type(self):
        return True
