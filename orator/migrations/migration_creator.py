# -*- coding: utf-8 -*-

import os
import inflection
import datetime
import errno
from .stubs import CREATE_STUB, UPDATE_STUB, BLANK_STUB


def mkdir_p(path):
    try:
        os.makedirs(path)
    except OSError as exc:
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise


class MigrationCreator(object):

    def create(self, name, path, table=None, create=False):
        """
        Create a new migration at the given path.

        :param name: The name of the migration
        :type name: str
        :param path: The path of the migrations
        :type path: str
        :param table: The table name
        :type table: str
        :param create: Whether it's a create migration or not
        :type create: bool

        :rtype: str
        """
        path = self._get_path(name, path)
        if not os.path.exists(os.path.dirname(path)):
            mkdir_p(os.path.dirname(path))

        parent = os.path.join(os.path.dirname(path), '__init__.py')
        if not os.path.exists(parent):
            with open(parent, 'w'):
                pass

        stub = self._get_stub(table, create)

        with open(path, 'w') as fh:
            fh.write(self._populate_stub(name, stub, table))

        return path

    def _get_stub(self, table, create):
        """
        Get the migration stub template

        :param table: The table name
        :type table: str

        :param create: Whether it's a create migration or not
        :type create: bool

        :rtype: str
        """
        if table is None:
            return BLANK_STUB
        else:
            if create:
                stub = CREATE_STUB
            else:
                stub = UPDATE_STUB

            return stub

    def _populate_stub(self, name, stub, table):
        """
        Populate the placeholders in the migration stub.

        :param name: The name of the migration
        :type name: str

        :param stub: The stub
        :type stub: str

        :param table: The table name
        :type table: str

        :rtype: str
        """
        stub = stub.replace('DummyClass', self._get_class_name(name))

        if table is not None:
            stub = stub.replace('dummy_table', table)

        return stub

    def _get_class_name(self, name):
        return inflection.camelize(name)

    def _get_path(self, name, path):
        return os.path.join(path, self._get_date_prefix() + '_' + name + '.py')

    def _get_date_prefix(self):
        return datetime.datetime.utcnow().strftime('%Y_%m_%d_%H%M%S')
