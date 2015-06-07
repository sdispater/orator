# -*- coding: utf-8 -*-

from ..model import Model


class Pivot(Model):

    __guarded__ = []

    def __init__(self, parent, attributes, table, exists=False):
        """
        :param parent: The parent model
        :type parent: Model

        :param attributes: The pivot attributes
        :type attributes: dict

        :param table: the pivot table
        :type table: str

        :param exists: Whether the pivot exists or not
        :type exists: bool
        """
        if attributes is None:
            attributes = {}

        super(Pivot, self).__init__()

        self.set_raw_attributes(attributes, True)

        self.set_table(table)

        self.set_connection(parent.get_connection_name())

        self.__parent = parent

        self.set_exists(exists)

        self.__timestamps__ = self.has_timestamps_attributes()

    def _set_keys_for_save_query(self, query):
        """
        Set the keys for a save update query.

        :param query: A Builder instance
        :type query: orator.orm.Builder

        :return: The Builder instance
        :rtype: orator.orm.Builder
        """
        query.where(self.__foreign_key, self.get_attribute(self.__foreign_key))

        return query.where(self.__other_key, self.get_attribute(self.__other_key))

    def delete(self):
        """
        Delete the pivot model record from the database.

        :rtype: int
        """
        return self._get_delete_query().delete()

    def _get_delete_query(self):
        """
        Get the query builder for a delete operation on the pivot.

        :rtype: orator.orm.Builder
        """
        foreign = self.get_attribute(self.__foreign_key)

        query = self.new_query().where(self.__foreign_key, foreign)

        return query.where(self.__other_key, self.get_attribute(self.__other_key))

    def has_timestamps_attributes(self):
        """
        Determine if the pivot has timestamps attributes.

        :rtype: bool
        """
        return self.get_created_at_column() in self.get_attributes()

    def get_foreign_key(self):
        return self.__foreign_key

    def get_other_key(self):
        return self.__other_key

    def set_pivot_keys(self, foreign_key, other_key):
        """
        Set the key names for the pivot model instance
        """
        self.__foreign_key = foreign_key
        self.__other_key = other_key

        return self

    def get_created_at_column(self):
        return self.__parent.get_created_at_column()

    def get_updated_at_column(self):
        return self.__parent.get_updated_at_column()

    def set_table(self, table):
        """
        Set the table associated with the model.

        :param table: The table name
        :type table: str
        """
        self.__table__ = table

    def get_table(self):
        """
        Get the table associated with the model.

        :return: The name of the table
        :rtype: str
        """
        return self.__table__
