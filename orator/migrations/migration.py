# -*- coding: utf-8 -*-

from orator import Model


class Migration(object):

    _connection = None
    schema = None

    def set_schema_builder(self, schema):
        self.schema = schema

    def get_connection(self):
        return self._connection
