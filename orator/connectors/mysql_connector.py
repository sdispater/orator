# -*- coding: utf-8 -*-

try:
    import MySQLdb as mysql
    from MySQLdb.cursors import DictCursor as cursor_class
    keys_fix = {
        'password': 'passwd',
        'database': 'db'
    }
except ImportError:
    try:
        import pymysql as mysql
        from pymysql.cursors import DictCursor as cursor_class
        keys_fix = {}
    except ImportError:
        mysql = None

from .connector import Connector


class MySQLConnector(Connector):

    RESERVED_KEYWORDS = [
        'log_queries', 'driver', 'prefix',
        'engine', 'collation',
        'name'
    ]

    SUPPORTED_PACKAGES = ['PyMySQL', 'mysqlclient']

    def connect(self, config):
        config = dict(config.items())
        for key, value in keys_fix.items():
            config[value] = config[key]
            del config[key]

        config['autocommit'] = True
        config['cursorclass'] = cursor_class

        return self.get_api().connect(**self.get_config(config))

    def get_default_config(self):
        return {
            'charset': 'utf8',
            'use_unicode': True
        }

    def get_api(self):
        return mysql
