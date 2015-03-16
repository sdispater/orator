# -*- coding: utf-8 -*-

import psycopg2
import psycopg2.extras

from .connector import Connector


class PostgresConnector(Connector):

    def connect(self, config):
        return self.get_api().connect(
            host=config['host'],
            database=config['database'],
            user=config['username'],
            password=config['password'],
            connection_factory=psycopg2.extras.DictConnection
        )

    def get_api(self):
        return psycopg2
