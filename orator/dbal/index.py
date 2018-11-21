# -*- coding: utf-8 -*-

from collections import OrderedDict
from .abstract_asset import AbstractAsset
from .identifier import Identifier


class Index(AbstractAsset):
    """
    An abstraction class for an index.
    """

    def __init__(
        self, name, columns, is_unique=False, is_primary=False, flags=None, options=None
    ):
        """
        Constructor.

        :param name: The index name
        :type name: str

        :param columns: The index columns
        :type columns: list

        :param is_unique: Whether the index is unique or not
        :type is_unique: bool

        :param is_primary: Whether the index is primary or not
        :type is_primary: bool

        :param flags: The index flags
        :type: dict
        """
        is_unique = is_unique or is_primary

        self._set_name(name)
        self._is_unique = is_unique
        self._is_primary = is_primary
        self._options = options or {}
        self._columns = OrderedDict()
        self._flags = OrderedDict()

        for column in columns:
            self._add_column(column)

        flags = flags or OrderedDict()
        for flag in flags:
            self.add_flag(flag)

    def _add_column(self, column):
        """
        Adds a new column.

        :param column: The column to add
        :type column: str
        """
        self._columns[column] = Identifier(column)

    def get_columns(self):
        """
        :rtype: list
        """
        return list(self._columns.keys())

    def get_quoted_columns(self, platform):
        """
        Returns the quoted representation of the column names
        the constraint is associated with.

        But only if they were defined with one or a column name
        is a keyword reserved by the platform.
        Otherwise the plain unquoted value as inserted is returned.

        :param platform: The platform to use for quotation.
        :type platform: Platform

        :rtype: list
        """
        columns = []

        for column in self._columns.values():
            columns.append(column.get_quoted_name(platform))

        return columns

    def get_unquoted_columns(self):
        return list(map(self._trim_quotes, self.get_columns()))

    def is_simple_index(self):
        """
        Is the index neither unique nor primary key?

        :rtype: bool
        """
        return not self._is_primary and not self._is_unique

    def is_unique(self):
        return self._is_unique

    def is_primary(self):
        return self._is_primary

    def has_column_at_position(self, column_name, pos=0):
        """
        :type column_name: str
        :type pos: int

        :rtype: bool
        """
        column_name = self._trim_quotes(column_name.lower())
        index_columns = [c.lower() for c in self.get_unquoted_columns()]

        return index_columns.index(column_name) == pos

    def spans_columns(self, column_names):
        """
        Checks if this index exactly spans the given column names in the correct order.

        :type column_names: list

        :rtype: bool
        """
        columns = self.get_columns()
        number_of_columns = len(columns)
        same_columns = True

        for i in range(number_of_columns):
            column = self._trim_quotes(columns[i].lower())
            if i >= len(column_names) or column != self._trim_quotes(
                column_names[i].lower()
            ):
                same_columns = False

        return same_columns

    def is_fullfilled_by(self, other):
        """
        Checks if the other index already fulfills
        all the indexing and constraint needs of the current one.

        :param other: The other index
        :type other: Index

        :rtype: bool
        """
        # allow the other index to be equally large only. It being larger is an option
        # but it creates a problem with scenarios of the kind PRIMARY KEY(foo,bar) UNIQUE(foo)
        if len(other.get_columns()) != len(self.get_columns()):
            return False

        # Check if columns are the same, and even in the same order
        if not self.spans_columns(other.get_columns()):
            return False

        if not self.same_partial_index(other):
            return False

        if self.is_simple_index():
            # this is a special case: If the current key is neither primary or unique,
            # any unique or primary key will always have the same effect
            # for the index and there cannot be any constraint overlaps.
            # This means a primary or unique index can always fulfill
            # the requirements of just an index that has no constraints.
            return True

        if other.is_primary() != self.is_primary():
            return False

        if other.is_unique() != self.is_unique():
            return False

        return True

    def same_partial_index(self, other):
        """
        Return whether the two indexes have the same partial index

        :param other: The other index
        :type other: Index

        :rtype: bool
        """
        if (
            self.has_option("where")
            and other.has_option("where")
            and self.get_option("where") == other.get_option("where")
        ):
            return True

        if not self.has_option("where") and not other.has_option("where"):
            return True

        return False

    def overrules(self, other):
        """
        Detects if the other index is a non-unique, non primary index
        that can be overwritten by this one.

        :param other: The other index
        :type other: Index

        :rtype: bool
        """
        if other.is_primary():
            return False
        elif self.is_simple_index() and other.is_unique():
            return False

        same_columns = self.spans_columns(other.get_columns())
        if (
            same_columns
            and (self.is_primary() or self.is_unique())
            and self.same_partial_index(other)
        ):
            return True

        return False

    def get_flags(self):
        """
        Returns platform specific flags for indexes.

        :rtype: list
        """
        return list(self._flags.keys())

    def add_flag(self, flag):
        """
        Adds Flag for an index that translates to platform specific handling.

        >>> index.add_flag('CLUSTERED')

        :type flag: str

        :rtype: Index
        """
        self._flags[flag.lower()] = True

        return self

    def has_flag(self, flag):
        """
        Does this index have a specific flag?

        :type flag: str

        :rtype: bool
        """
        return flag.lower() in self._flags

    def remove_flag(self, flag):
        """
        Removes a flag.

        :type flag: str
        """
        if self.has_flag(flag):
            del self._flags[flag.lower()]

    def has_option(self, name):
        return name in self._options

    def get_option(self, name):
        return self._options[name]

    def get_options(self):
        return self._options
