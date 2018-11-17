# -*- coding: utf-8 -*-

import re
from collections import OrderedDict
from .column import Column
from .abstract_asset import AbstractAsset
from .index import Index
from .foreign_key_constraint import ForeignKeyConstraint
from .exceptions import (
    DBALException,
    IndexDoesNotExist,
    IndexAlreadyExists,
    IndexNameInvalid,
    ColumnDoesNotExist,
    ColumnAlreadyExists,
    ForeignKeyDoesNotExist,
)


class Table(AbstractAsset):
    def __init__(
        self, table_name, columns=None, indexes=None, fk_constraints=None, options=None
    ):
        self._set_name(table_name)
        self._primary_key_name = False
        self._columns = OrderedDict()
        self._indexes = OrderedDict()
        self._implicit_indexes = OrderedDict()
        self._fk_constraints = OrderedDict()
        self._options = options or {}

        columns = columns or []
        indexes = indexes or []
        fk_constraints = fk_constraints or []

        columns = columns.values() if isinstance(columns, dict) else columns
        for column in columns:
            self._add_column(column)

        indexes = indexes.values() if isinstance(indexes, dict) else indexes
        for index in indexes:
            self._add_index(index)

        fk_constraints = (
            fk_constraints.values()
            if isinstance(fk_constraints, dict)
            else fk_constraints
        )
        for constraint in fk_constraints:
            self._add_foreign_key_constraint(constraint)

    def _get_max_identifier_length(self):
        return 63

    def set_primary_key(self, columns, index_name=False):
        """
        Set the primary key.

        :type columns: list
        :type index_name: str or bool

        :rtype: Table
        """
        self._add_index(
            self._create_index(columns, index_name or "primary", True, True)
        )

        for column_name in columns:
            column = self.get_column(column_name)
            column.set_notnull(True)

        return self

    def add_index(self, columns, name=None, flags=None, options=None):
        if not name:
            name = self._generate_identifier_name(
                [self.get_name()] + columns, "idx", self._get_max_identifier_length()
            )

        return self._add_index(
            self._create_index(columns, name, False, False, flags, options)
        )

    def drop_primary_key(self):
        """
        Drop the primary key from this table.
        """
        self.drop_index(self._primary_key_name)
        self._primary_key_name = False

    def drop_index(self, name):
        """
        Drops an index from this table.

        :param name: The index name
        :type name: str
        """
        name = self._normalize_identifier(name)
        if not self.has_index(name):
            raise IndexDoesNotExist(name, self._name)

        del self._indexes[name]

    def add_unique_index(self, columns, name=None, options=None):
        if not name:
            name = self._generate_identifier_name(
                [self.get_name()] + columns, "uniq", self._get_max_identifier_length()
            )

        return self._add_index(
            self._create_index(columns, name, True, False, None, options)
        )

    def rename_index(self, old_name, new_name=None):
        """
        Renames an index.

        :param old_name: The name of the index to rename from.
        :type old_name: str

        :param new_name: The name of the index to rename to.
        :type new_name: str or None

        :rtype: Table
        """
        old_name = self._normalize_identifier(old_name)
        normalized_new_name = self._normalize_identifier(new_name)

        if old_name == normalized_new_name:
            return self

        if not self.has_index(old_name):
            raise IndexDoesNotExist(old_name, self._name)

        if self.has_index(normalized_new_name):
            raise IndexAlreadyExists(normalized_new_name, self._name)

        old_index = self._indexes[old_name]

        if old_index.is_primary():
            self.drop_primary_key()

            return self.set_primary_key(old_index.get_columns(), new_name)

        del self._indexes[old_name]

        if old_index.is_unique():
            return self.add_unique_index(old_index.get_columns(), new_name)

        return self.add_index(old_index.get_columns(), new_name, old_index.get_flags())

    def columns_are_indexed(self, columns):
        """
        Checks if an index begins in the order of the given columns.

        :type columns: list

        :rtype: bool
        """
        for index in self._indexes.values():
            if index.spans_columns(columns):
                return True

        return False

    def _create_index(
        self, columns, name, is_unique, is_primary, flags=None, options=None
    ):
        """
        Creates an Index instance.

        :param columns: The index columns
        :type columns: list

        :param name: The index name
        :type name: str

        :param is_unique: Whether the index is unique or not
        :type is_unique: bool

        :param is_primary: Whether the index is primary or not
        :type is_primary: bool

        :param flags: The index flags
        :type: dict

        :param options: The options
        :type options: dict

        :rtype: Index
        """
        if re.match("[^a-zA-Z0-9_]+", self._normalize_identifier(name)):
            raise IndexNameInvalid(name)

        for column in columns:
            if isinstance(column, dict):
                column = list(column.keys())[0]

            if not self.has_column(column):
                raise ColumnDoesNotExist(column, self._name)

        return Index(name, columns, is_unique, is_primary, flags, options)

    def add_column(self, name, type_name, options=None):
        """
        Adds a new column.

        :param name: The column name
        :type name: str

        :param type_name: The column type
        :type type_name: str

        :param options: The column options
        :type options: dict

        :rtype: Column
        """
        column = Column(name, type_name, options)

        self._add_column(column)

        return column

    def change_column(self, name, options):
        """
        Changes column details.

        :param name: The column to change.
        :type name: str

        :param options: The new options.
        :type options: str

        :rtype: Table
        """
        column = self.get_column(name)
        column.set_options(options)

        return self

    def drop_column(self, name):
        """
        Drops a Column from the Table

        :param name: The name of the column
        :type name: str

        :rtype: Table
        """
        name = self._normalize_identifier(name)
        del self._columns[name]

        return self

    def add_foreign_key_constraint(
        self,
        foreign_table,
        local_columns,
        foreign_columns,
        options=None,
        constraint_name=None,
    ):
        """
        Adds a foreign key constraint.

        Name is inferred from the local columns.

        :param foreign_table: Table instance or table name
        :type foreign_table: Table or str

        :type local_columns: list

        :type foreign_columns: list

        :type options: dict

        :type constraint_name: str or None

        :rtype: Table
        """
        if not constraint_name:
            constraint_name = self._generate_identifier_name(
                [self.get_name()] + local_columns,
                "fk",
                self._get_max_identifier_length(),
            )

        return self.add_named_foreign_key_constraint(
            constraint_name, foreign_table, local_columns, foreign_columns, options
        )

    def add_named_foreign_key_constraint(
        self, name, foreign_table, local_columns, foreign_columns, options
    ):
        """
        Adds a foreign key constraint with a given name.

        :param name: The constraint name
        :type name: str

        :param foreign_table: Table instance or table name
        :type foreign_table: Table or str

        :type local_columns: list

        :type foreign_columns: list

        :type options: dict

        :rtype: Table
        """
        if isinstance(foreign_table, Table):
            for column in foreign_columns:
                if not foreign_table.has_column(column):
                    raise ColumnDoesNotExist(column, foreign_table.get_name())

        for column in local_columns:
            if not self.has_column(column):
                raise ColumnDoesNotExist(column, self._name)

        constraint = ForeignKeyConstraint(
            local_columns, foreign_table, foreign_columns, name, options
        )

        self._add_foreign_key_constraint(constraint)

        return self

    def add_option(self, name, value):
        self._options[name] = value

    def _add_column(self, column):
        column_name = self._normalize_identifier(column.get_name())

        if column_name in self._columns:
            raise ColumnAlreadyExists(column_name, self._name)

        self._columns[column_name] = column

        return self

    def _add_index(self, index):
        """
        Adds an index to the table.

        :param index: The index to add
        :type index: Index

        :rtype: Table
        """
        index_name = index.get_name()
        index_name = self._normalize_identifier(index_name)
        replaced_implicit_indexes = []

        for name, implicit_index in self._implicit_indexes.items():
            if implicit_index.is_fullfilled_by(index) and name in self._indexes:
                replaced_implicit_indexes.append(name)

        already_exists = (
            index_name in self._indexes
            and index_name not in replaced_implicit_indexes
            or self._primary_key_name is not False
            and index.is_primary()
        )
        if already_exists:
            raise IndexAlreadyExists(index_name, self._name)

        for name in replaced_implicit_indexes:
            del self._indexes[name]
            del self._implicit_indexes[name]

        if index.is_primary():
            self._primary_key_name = index_name

        self._indexes[index_name] = index

        return self

    def _add_foreign_key_constraint(self, constraint):
        """
        Adds a foreign key constraint.

        :param constraint: The constraint to add
        :type constraint: ForeignKeyConstraint

        :rtype: Table
        """
        constraint.set_local_table(self)

        if constraint.get_name():
            name = constraint.get_name()
        else:
            name = self._generate_identifier_name(
                [self.get_name()] + constraint.get_local_columns(),
                "fk",
                self._get_max_identifier_length(),
            )

        name = self._normalize_identifier(name)

        self._fk_constraints[name] = constraint

        # Add an explicit index on the foreign key columns.
        # If there is already an index that fulfils this requirements drop the request.
        # In the case of __init__ calling this method during hydration from schema-details
        # all the explicitly added indexes lead to duplicates.
        # This creates computation overhead in this case, however no duplicate indexes
        # are ever added (based on columns).
        index_name = self._generate_identifier_name(
            [self.get_name()] + constraint.get_columns(),
            "idx",
            self._get_max_identifier_length(),
        )
        index_candidate = self._create_index(
            constraint.get_columns(), index_name, False, False
        )

        for existing_index in self._indexes.values():
            if index_candidate.is_fullfilled_by(existing_index):
                return

        # self._add_index(index_candidate)
        # self._implicit_indexes[self._normalize_identifier(index_name)] = index_candidate

        return self

    def has_foreign_key(self, name):
        """
        Returns whether this table has a foreign key constraint with the given name.

        :param name: The constraint name
        :type name: str

        :rtype: bool
        """
        name = self._normalize_identifier(name)

        return name in self._fk_constraints

    def get_foreign_key(self, name):
        """
        Returns the foreign key constraint with the given name.

        :param name: The constraint name
        :type name: str

        :rtype: ForeignKeyConstraint
        """
        name = self._normalize_identifier(name)

        if not self.has_foreign_key(name):
            raise ForeignKeyDoesNotExist(name, self._name)

        return self._fk_constraints[name]

    def remove_foreign_key(self, name):
        """
        Removes the foreign key constraint with the given name.

        :param name: The constraint name
        :type name: str
        """
        name = self._normalize_identifier(name)

        if not self.has_foreign_key(name):
            raise ForeignKeyDoesNotExist(name, self._name)

        del self._fk_constraints[name]

    def get_columns(self):
        columns = self._columns

        pk_cols = []
        fk_cols = []

        if self.has_primary_key():
            pk_cols = self.get_primary_key().get_columns()

        for fk in self.get_foreign_keys().values():
            fk_cols += fk.get_columns()

        col_names = pk_cols + fk_cols
        col_names = [x for x in col_names if x not in columns]
        col_names += list(columns.keys())

        return columns

    def has_column(self, column):
        return self._normalize_identifier(column) in self._columns

    def get_column(self, column):
        column = self._normalize_identifier(column)

        if not self.has_column(column):
            raise ColumnDoesNotExist(column, self._name)

        return self._columns[column]

    def get_primary_key(self):
        """
        Returns the primary key

        :rtype: Index or None
        """
        if not self.has_primary_key():
            return None

        return self.get_index(self._primary_key_name)

    def get_primary_key_columns(self):
        """
        Returns the primary key columns.

        :rtype: list
        """
        if not self.has_primary_key():
            raise DBALException('Table "%s" has no primary key.' % self.get_name())

        return self.get_primary_key().get_columns()

    def has_primary_key(self):
        """
        Returns whether this table has a primary key.

        :rtype: bool
        """
        if not self._primary_key_name:
            return False

        return self.has_index(self._primary_key_name)

    def has_index(self, name):
        """
        Returns whether this table has an Index with the given name.

        :param name: The index name
        :type name: str

        :rtype: bool
        """
        name = self._normalize_identifier(name)

        return name in self._indexes

    def get_index(self, name):
        """
        Returns the Index with the given name.

        :param name: The index name
        :type name: str

        :rtype: Index
        """
        name = self._normalize_identifier(name)
        if not self.has_index(name):
            raise IndexDoesNotExist(name, self._name)

        return self._indexes[name]

    def get_indexes(self):
        return self._indexes

    def get_foreign_keys(self):
        return self._fk_constraints

    def has_option(self, name):
        return name in self._options

    def get_option(self, name):
        return self._options[name]

    def get_options(self):
        return self._options

    def get_name(self):
        return self._name

    def clone(self):
        table = Table(self._name)

        table._primary_key_name = self._primary_key_name

        for k, column in self._columns.items():
            table._columns[k] = Column(
                column.get_name(), column.get_type(), column.to_dict()
            )

        for k, index in self._indexes.items():
            table._indexes[k] = Index(
                index.get_name(),
                index.get_columns(),
                index.is_unique(),
                index.is_primary(),
                index.get_flags(),
                index.get_options(),
            )

        for k, fk in self._fk_constraints.items():
            table._fk_constraints[k] = ForeignKeyConstraint(
                fk.get_local_columns(),
                fk.get_foreign_table_name(),
                fk.get_foreign_columns(),
                fk.get_name(),
                fk.get_options(),
            )
            table._fk_constraints[k].set_local_table(table)

        return table

    def _normalize_identifier(self, identifier):
        """
        Normalizes a given identifier.

        Trims quotes and lowercases the given identifier.

        :param identifier: The identifier to normalize.
        :type identifier: str

        :rtype: str
        """
        return self._trim_quotes(identifier.lower())
