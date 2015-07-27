# -*- coding: utf-8 -*-

from orator import Model


class Migration(object):

    _connection = None
    transactional = True

    @property
    def schema(self):
        return self._connection.get_schema_builder()

    @property
    def db(self):
        return self._connection

    def get_connection(self):
        return self._connection

    def set_connection(self, connection):
        self._connection = connection
