# -*- coding: utf-8 -*-

try:
    import MySQLdb as mysql
    from MySQLdb.cursors import DictCursor as cursor_class
except ImportError:
    try:
        import pymysql as mysql
        from pymysql.cursors import DictCursor as cursor_class
    except ImportError:
        mysql = None

from .connector import Connector


class MySqlConnector(Connector):

    def connect(self, config):
        config['autocommit'] = True
        config['cursorclass'] = cursor_class

        return self.get_api().connect(
            **dict(filter(lambda x: x[0] != 'driver', config.items()))
        )

    def get_api(self):
        return mysql
