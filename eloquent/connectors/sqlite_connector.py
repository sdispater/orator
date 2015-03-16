# -*- coding: utf-8 -*-

import sqlite3

from .connector import Connector


class SQLiteConnector(Connector):

    def get_api(self):
        return sqlite3
