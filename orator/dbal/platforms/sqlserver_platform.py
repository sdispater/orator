# -*- coding: utf-8 -*-

from .platform import Platform
from .keywords.sqlserver_keywords import SQLServerKeywords
from ..identifier import Identifier

class SQLServerPlatform(Platform):

    LENGTH_LIMIT_TINYTEXT = 255
    LENGTH_LIMIT_TEXT = 65535
    LENGTH_LIMIT_MEDIUMTEXT = 16777215

    LENGTH_LIMIT_TINYBLOB = 255
    LENGTH_LIMIT_BLOB = 65535
    LENGTH_LIMIT_MEDIUMBLOB = 16777215

    INTERNAL_TYPE_MAPPING = {
        'bigint': 'bigint',
        'numeric': 'decimal',
        'bit': 'boolean',
        'smallint': 'smallint',
        'decimal': 'decimal',
        'smallmoney': 'integer',
        'int': 'integer',
        'tinyint': 'smallint',
        'money': 'integer',
        'float': 'float',
        'real': 'float',
        'smalldatetime': 'datetime',
        'datetime': 'datetime',
        'char': 'string',
        'varchar': 'string',
        'text': 'text',
        'nchar': 'string',
        'nvarchar': 'string',
        'ntext': 'text',
        'binary': 'binary',
        'varbinary': 'binary',
        'image': 'blob',
        'uniqueidentifier': 'guid',
        'xml': 'string',
        'date': 'date',
        'datetime2': 'datetime',
        'datetimeoffset': 'datetime',
        'time': 'time'
    }
