# -*- coding: utf-8 -*-

from collections import OrderedDict
from .abstract_asset import AbstractAsset
from .identifier import Identifier


class ForeignKeyConstraint(AbstractAsset):
    """
    An abstraction class for a foreign key constraint.
    """

    def __init__(
        self,
        local_column_names,
        foreign_table_name,
        foreign_column_names,
        name=None,
        options=None,
    ):
        """
        Constructor.

        :param local_column_names: Names of the referencing table columns.
        :type local_column_names: list

        :param foreign_table_name: Referenced table.
        :type foreign_table_name: str

        :param foreign_column_names: Names of the referenced table columns.
        :type foreign_column_names: list

        :param name: Name of the foreign key constraint.
        :type name: str or None

        :param options: Options associated with the foreign key constraint.
        :type options: dict or None
        """
        from .table import Table

        self._set_name(name)

        self._local_table = None

        self._local_column_names = OrderedDict()
        if local_column_names:
            for column_name in local_column_names:
                self._local_column_names[column_name] = Identifier(column_name)

        if isinstance(foreign_table_name, Table):
            self._foreign_table_name = foreign_table_name
        else:
            self._foreign_table_name = Identifier(foreign_table_name)

        self._foreign_column_names = OrderedDict()
        if foreign_column_names:
            for column_name in foreign_column_names:
                self._foreign_column_names[column_name] = Identifier(column_name)

        self._options = options or {}

    def get_local_table_name(self):
        """
        Returns the name of the referencing table
        the foreign key constraint is associated with.

        :rtype: str
        """
        self._local_table.get_name()

    def set_local_table(self, table):
        """
        Sets the Table instance of the referencing table
        the foreign key constraint is associated with.

        :param table: Instance of the referencing table.
        :type table: Table
        """
        self._local_table = table

    def get_local_table(self):
        """
        :rtype: Table
        """
        return self._local_table

    def get_local_columns(self):
        """
        Returns the names of the referencing table columns
        the foreign key constraint is associated with.

        :rtype: list
        """
        return list(self._local_column_names.keys())

    def get_quoted_local_columns(self, platform):
        """
        Returns the quoted representation of the referencing table column names
        the foreign key constraint is associated with.

        But only if they were defined with one or the referencing table column name
        is a keyword reserved by the platform.
        Otherwise the plain unquoted value as inserted is returned.

        :param platform: The platform to use for quotation.
        :type platform: Platform

        :rtype: list
        """
        columns = []

        for column in self._local_column_names.values():
            columns.append(column.get_quoted_name(platform))

        return columns

    def get_unquoted_local_columns(self):
        """
        Returns unquoted representation of local table
        column names for comparison with other FK.

        :rtype: list
        """
        return list(map(self._trim_quotes, self.get_local_columns()))

    def get_columns(self):
        return self.get_local_columns()

    def get_quoted_columns(self, platform):
        """
        Returns the quoted representation of the referencing table column names
        the foreign key constraint is associated with.

        But only if they were defined with one or the referencing table column name
        is a keyword reserved by the platform.
        Otherwise the plain unquoted value as inserted is returned.

        :param platform: The platform to use for quotation.
        :type platform: Platform

        :rtype: list
        """
        return self.get_quoted_local_columns(platform)

    def get_foreign_table_name(self):
        """
        Returns the name of the referenced table
        the foreign key constraint is associated with.

        :rtype: str
        """
        return self._foreign_table_name.get_name()

    def get_unqualified_foreign_table_name(self):
        """
        Returns the non-schema qualified foreign table name.

        :rtype: str
        """
        parts = self.get_foreign_table_name().split(".")

        return parts[-1].lower()

    def get_quoted_foreign_table_name(self, platform):
        """
        Returns the quoted representation of the referenced table name
        the foreign key constraint is associated with.

        But only if it was defined with one or the referenced table name
        is a keyword reserved by the platform.
        Otherwise the plain unquoted value as inserted is returned.

        :param platform: The platform to use for quotation.
        :type platform: Platform

        :rtype: str
        """
        return self._foreign_table_name.get_quoted_name(platform)

    def get_foreign_columns(self):
        """
        Returns the names of the referenced table columns
        the foreign key constraint is associated with.

        :rtype: list
        """
        return list(self._foreign_column_names.keys())

    def get_quoted_foreign_columns(self, platform):
        """
        Returns the quoted representation of the referenced table column names
        the foreign key constraint is associated with.

        But only if they were defined with one or the referenced table column name
        is a keyword reserved by the platform.
        Otherwise the plain unquoted value as inserted is returned.

        :param platform: The platform to use for quotation.
        :type platform: Platform

        :rtype: list
        """
        columns = []

        for column in self._foreign_column_names.values():
            columns.append(column.get_quoted_name(platform))

        return columns

    def get_unquoted_foreign_columns(self):
        """
        Returns unquoted representation of foreign table
        column names for comparison with other FK.

        :rtype: list
        """
        return list(map(self._trim_quotes, self.get_foreign_columns()))

    def has_option(self, name):
        return name in self._options

    def get_option(self, name):
        return self._options[name]

    def get_options(self):
        return self._options

    def on_update(self):
        """
        Returns the referential action for UPDATE operations
        on the referenced table the foreign key constraint is associated with.

        :rtype: str or None
        """
        return self._on_event("on_update")

    def on_delete(self):
        """
        Returns the referential action for DELETE operations
        on the referenced table the foreign key constraint is associated with.

        :rtype: str or None
        """
        return self._on_event("on_delete")

    def _on_event(self, event):
        """
        Returns the referential action for a given database operation
        on the referenced table the foreign key constraint is associated with.

        :param event: Name of the database operation/event to return the referential action for.
        :type event: str

        :rtype: str or None
        """
        if self.has_option(event):
            on_event = self.get_option(event).upper()

            if on_event not in ["NO ACTION", "RESTRICT"]:
                return on_event

        return False

    def intersects_index_columns(self, index):
        """
        Checks whether this foreign key constraint intersects the given index columns.

        Returns `true` if at least one of this foreign key's local columns
        matches one of the given index's columns, `false` otherwise.

        :param index: The index to be checked against.
        :type index: Index

        :rtype: bool
        """
