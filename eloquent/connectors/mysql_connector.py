# -*- coding: utf-8 -*-

try:
    import MySQLdb as mysql
except ImportError:
    try:
        import pymysql as mysql
    except ImportError:
        mysql = None

from .connector import Connector


class MySqlConnector(Connector):

    def get_api(self):
        return mysql
