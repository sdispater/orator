# -*- coding: utf-8 -*-

from .platform import Platform
from .keywords.mssql_keywords import MsSQLKeywords
from ..identifier import Identifier

class MsSQLPlatform(Platform):

    LENGTH_LIMIT_TINYTEXT = 255
    LENGTH_LIMIT_TEXT = 65535
    LENGTH_LIMIT_MEDIUMTEXT = 16777215

    LENGTH_LIMIT_TINYBLOB = 255
    LENGTH_LIMIT_BLOB = 65535
    LENGTH_LIMIT_MEDIUMBLOB = 16777215

    INTERNAL_TYPE_MAPPING = {
        'tinyint': 'tinyint',
        'smallint': 'smallint',
        'mediumint': 'int',
        'int': 'int',
        'integer': 'int',
        'bigint': 'bigint',
        'int8': 'bigint',
        'enum': 'int',
        'float': 'float',
        'double': 'float',
        'real': 'real',
        'decimal': 'decimal',
        'numeric': 'numeric',
        'bool': 'bit',
        'boolean': 'bit',
        'tinytext': 'text',
        'mediumtext': 'text',
        'longtext': 'text',
        'text': 'text',
        'varchar': 'varchar',
        'string': 'nvarchar',
        'char': 'char',
        'set': 'nvarchar',
        'date': 'date',
        'datetime': 'datetime',
        'timestamp': 'timestamp',
        'time': 'time',
        'year': 'datetime',
        'longblob': 'varbinary',
        'blob': 'varbinary',
        'mediumblob': 'varbinary',
        'tinyblob': 'varbinary',
        'binary': 'binary',
        'varbinary': 'varbinary',
    }
