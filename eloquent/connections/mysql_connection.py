# -*- coding: utf-8 -*-

from .connection import Connection
from ..query.processors.mysql_processor import MySqlQueryProcessor


class MySqlConnection(Connection):

    def get_default_post_processor(self):
        return MySqlQueryProcessor()
