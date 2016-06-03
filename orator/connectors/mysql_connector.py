# -*- coding: utf-8 -*-

import re

try:
    import MySQLdb as mysql
    from MySQLdb.cursors import DictCursor as cursor_class
    keys_fix = {
        'password': 'passwd',
        'database': 'db'
    }
except ImportError as e:
    try:
        import pymysql as mysql
        from pymysql.cursors import DictCursor as cursor_class
        keys_fix = {}
    except ImportError as e:
        mysql = None
        cursor_class = object

from .connector import Connector
from ..utils.qmarker import qmark, denullify


class DictCursor(cursor_class):

    def execute(self, query, args=None):
        query = qmark(query)

        return super(DictCursor, self).execute(query, args)

    def executemany(self, query, args):
        query = qmark(query)

        return super(DictCursor, self).executemany(
            query, denullify(args)
        )


class MySQLConnector(Connector):

    RESERVED_KEYWORDS = [
        'log_queries', 'driver', 'prefix',
        'engine', 'collation',
        'name', 'use_qmark'
    ]

    SUPPORTED_PACKAGES = ['PyMySQL', 'mysqlclient']

    def connect(self, config):
        config = dict(config.items())
        for key, value in keys_fix.items():
            config[value] = config[key]
            del config[key]

        config['autocommit'] = True
        config['cursorclass'] = self.get_cursor_class(config)

        return self.get_api().connect(**self.get_config(config))

    def get_default_config(self):
        return {
            'charset': 'utf8',
            'use_unicode': True
        }

    def get_cursor_class(self, config):
        if config.get('use_qmark'):
            return DictCursor

        return cursor_class

    def get_api(self):
        return mysql
