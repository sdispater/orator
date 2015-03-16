# -*- coding: utf-8 -*-

import sqlite3

from .connector import Connector


def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d


class SQLiteConnector(Connector):

    def connect(self, config):
        connection = self.get_api().connect(config['database'])
        connection.isolation_level = None
        connection.row_factory = dict_factory

        return connection

    def get_api(self):
        return sqlite3
