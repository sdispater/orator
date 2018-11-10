# -*- coding: utf-8 -*-

from collections import OrderedDict
from .platform import Platform
from .keywords.sqlite_keywords import SQLiteKeywords
from ..table import Table
from ..index import Index
from ..column import Column
from ..identifier import Identifier
from ..foreign_key_constraint import ForeignKeyConstraint
from ..exceptions import DBALException


class SQLitePlatform(Platform):

    INTERNAL_TYPE_MAPPING = {
        "boolean": "boolean",
        "tinyint": "boolean",
        "smallint": "smallint",
        "mediumint": "integer",
        "int": "integer",
        "integer": "integer",
        "serial": "integer",
        "bigint": "bigint",
        "bigserial": "bigint",
        "clob": "text",
        "tinytext": "text",
        "mediumtext": "text",
        "longtext": "text",
        "text": "text",
        "varchar": "string",
        "longvarchar": "string",
        "varchar2": "string",
        "nvarchar": "string",
        "image": "string",
        "ntext": "string",
        "char": "string",
        "date": "date",
        "datetime": "datetime",
        "timestamp": "datetime",
        "time": "time",
        "float": "float",
        "double": "float",
        "double precision": "float",
        "real": "float",
        "decimal": "decimal",
        "numeric": "decimal",
        "blob": "blob",
    }

    def get_list_table_columns_sql(self, table):
        table = table.replace(".", "__")

        return "PRAGMA table_info('%s')" % table

    def get_list_table_indexes_sql(self, table):
        table = table.replace(".", "__")

        return "PRAGMA index_list('%s')" % table

    def get_list_table_foreign_keys_sql(self, table):
        table = table.replace(".", "__")

        return "PRAGMA foreign_key_list('%s')" % table

    def get_pre_alter_table_index_foreign_key_sql(self, diff):
        """
        :param diff: The table diff
        :type diff: orator.dbal.table_diff.TableDiff

        :rtype: list
        """
        if not isinstance(diff.from_table, Table):
            raise DBALException(
                "Sqlite platform requires for alter table the table"
                "diff with reference to original table schema"
            )

        sql = []
        for index in diff.from_table.get_indexes().values():
            if not index.is_primary():
                sql.append(self.get_drop_index_sql(index, diff.name))

        return sql

    def get_post_alter_table_index_foreign_key_sql(self, diff):
        """
        :param diff: The table diff
        :type diff: orator.dbal.table_diff.TableDiff

        :rtype: list
        """
        if not isinstance(diff.from_table, Table):
            raise DBALException(
                "Sqlite platform requires for alter table the table"
                "diff with reference to original table schema"
            )

        sql = []

        if diff.new_name:
            table_name = diff.get_new_name()
        else:
            table_name = diff.get_name(self)

        for index in self._get_indexes_in_altered_table(diff).values():
            if index.is_primary():
                continue

            sql.append(
                self.get_create_index_sql(index, table_name.get_quoted_name(self))
            )

        return sql

    def get_create_table_sql(self, table, create_flags=None):
        if not create_flags:
            create_flags = self.CREATE_INDEXES | self.CREATE_FOREIGNKEYS

        return super(SQLitePlatform, self).get_create_table_sql(table, create_flags)

    def _get_create_table_sql(self, table_name, columns, options=None):
        table_name = table_name.replace(".", "__")
        query_fields = self.get_column_declaration_list_sql(columns)

        if options.get("unique_constraints"):
            for name, definition in options["unique_constraints"].items():
                query_fields += ", %s" % self.get_unique_constraint_declaration_sql(
                    name, definition
                )

        if options.get("primary"):
            key_columns = options["primary"]
            query_fields += ", PRIMARY KEY(%s)" % ", ".join(key_columns)

        if options.get("foreign_keys"):
            for foreign_key in options["foreign_keys"]:
                query_fields += ", %s" % self.get_foreign_key_declaration_sql(
                    foreign_key
                )

        query = ["CREATE TABLE %s (%s)" % (table_name, query_fields)]

        if options.get("alter"):
            return query

        if options.get("indexes"):
            for index_def in options["indexes"].values():
                query.append(self.get_create_index_sql(index_def, table_name))

        if options.get("unique"):
            for index_def in options["unique"].values():
                query.append(self.get_create_index_sql(index_def, table_name))

        return query

    def get_foreign_key_declaration_sql(self, foreign_key):
        return super(SQLitePlatform, self).get_foreign_key_declaration_sql(
            ForeignKeyConstraint(
                foreign_key.get_quoted_local_columns(self),
                foreign_key.get_quoted_foreign_table_name(self).replace(".", "__"),
                foreign_key.get_quoted_foreign_columns(self),
                foreign_key.get_name(),
                foreign_key.get_options(),
            )
        )

    def get_advanced_foreign_key_options_sql(self, foreign_key):
        query = super(SQLitePlatform, self).get_advanced_foreign_key_options_sql(
            foreign_key
        )

        deferrable = (
            foreign_key.has_option("deferrable")
            and foreign_key.get_option("deferrable") is not False
        )
        if deferrable:
            query += " DEFERRABLE"
        else:
            query += " NOT DEFERRABLE"

        query += " INITIALLY"

        deferred = (
            foreign_key.has_option("deferred")
            and foreign_key.get_option("deferred") is not False
        )
        if deferred:
            query += " DEFERRED"
        else:
            query += " IMMEDIATE"

        return query

    def get_alter_table_sql(self, diff):
        """
        Get the ALTER TABLE SQL statement

        :param diff: The table diff
        :type diff: orator.dbal.table_diff.TableDiff

        :rtype: list
        """
        sql = self._get_simple_alter_table_sql(diff)
        if sql is not False:
            return sql

        from_table = diff.from_table
        if not isinstance(from_table, Table):
            raise DBALException(
                "SQLite platform requires for the alter table the table diff "
                "referencing the original table"
            )

        table = from_table.clone()
        columns = OrderedDict()
        old_column_names = OrderedDict()
        new_column_names = OrderedDict()
        column_sql = []
        for column_name, column in table.get_columns().items():
            column_name = column_name.lower()
            columns[column_name] = column
            old_column_names[column_name] = column.get_quoted_name(self)
            new_column_names[column_name] = column.get_quoted_name(self)

        for column_name, column in diff.removed_columns.items():
            column_name = column_name.lower()
            if column_name in columns:
                del columns[column_name]
                del old_column_names[column_name]
                del new_column_names[column_name]

        for old_column_name, column in diff.renamed_columns.items():
            old_column_name = old_column_name.lower()
            if old_column_name in columns:
                del columns[old_column_name]

            columns[column.get_name().lower()] = column

            if old_column_name in new_column_names:
                new_column_names[old_column_name] = column.get_quoted_name(self)

        for old_column_name, column_diff in diff.changed_columns.items():
            if old_column_name in columns:
                del columns[old_column_name]

            columns[column_diff.column.get_name().lower()] = column_diff.column

            if old_column_name in new_column_names:
                new_column_names[old_column_name] = column_diff.column.get_quoted_name(
                    self
                )

        for column_name, column in diff.added_columns.items():
            columns[column_name.lower()] = column

        table_sql = []

        data_table = Table("__temp__" + table.get_name())
        new_table = Table(
            table.get_quoted_name(self),
            columns,
            self._get_primary_index_in_altered_table(diff),
            self._get_foreign_keys_in_altered_table(diff),
            table.get_options(),
        )
        new_table.add_option("alter", True)

        sql = self.get_pre_alter_table_index_foreign_key_sql(diff)
        sql.append(
            "CREATE TEMPORARY TABLE %s AS SELECT %s FROM %s"
            % (
                data_table.get_quoted_name(self),
                ", ".join(old_column_names.values()),
                table.get_quoted_name(self),
            )
        )
        sql.append(self.get_drop_table_sql(from_table))

        sql += self.get_create_table_sql(new_table)
        sql.append(
            "INSERT INTO %s (%s) SELECT %s FROM %s"
            % (
                new_table.get_quoted_name(self),
                ", ".join(new_column_names.values()),
                ", ".join(old_column_names.values()),
                data_table.get_name(),
            )
        )
        sql.append(self.get_drop_table_sql(data_table))

        sql += self.get_post_alter_table_index_foreign_key_sql(diff)

        return sql

    def _get_simple_alter_table_sql(self, diff):
        for old_column_name, column_diff in diff.changed_columns.items():
            if (
                not isinstance(column_diff.from_column, Column)
                or not isinstance(column_diff.column, Column)
                or not column_diff.column.get_autoincrement()
                or column_diff.column.get_type().lower() != "integer"
            ):
                continue

            if not column_diff.has_changed("type") and not column_diff.has_changed(
                "unsigned"
            ):
                del diff.changed_columns[old_column_name]

                continue

            from_column_type = column_diff.column.get_type()

            if from_column_type == "smallint" or from_column_type == "bigint":
                del diff.changed_columns[old_column_name]

        if any(
            [
                not diff.renamed_columns,
                not diff.added_foreign_keys,
                not diff.added_indexes,
                not diff.changed_columns,
                not diff.changed_foreign_keys,
                not diff.changed_indexes,
                not diff.removed_columns,
                not diff.removed_foreign_keys,
                not diff.removed_indexes,
                not diff.renamed_indexes,
            ]
        ):
            return False

        table = Table(diff.name)

        sql = []
        table_sql = []
        column_sql = []

        for column in diff.added_columns.values():
            field = {"unique": None, "autoincrement": None, "default": None}
            field.update(column.to_dict())

            type_ = field["type"]
            if (
                "column_definition" in field
                or field["autoincrement"]
                or field["unique"]
            ):
                return False
            elif (
                type_ == "datetime"
                and field["default"] == self.get_current_timestamp_sql()
            ):
                return False
            elif type_ == "date" and field["default"] == self.get_current_date_sql():
                return False
            elif type_ == "time" and field["default"] == self.get_current_time_sql():
                return False

            field["name"] = column.get_quoted_name(self)
            if field["type"].lower() == "string" and field["length"] is None:
                field["length"] = 255

            sql.append(
                "ALTER TABLE "
                + table.get_quoted_name(self)
                + " ADD COLUMN "
                + self.get_column_declaration_sql(field["name"], field)
            )

        if diff.new_name is not False:
            new_table = Identifier(diff.new_name)
            sql.append(
                "ALTER TABLE "
                + table.get_quoted_name(self)
                + " RENAME TO "
                + new_table.get_quoted_name(self)
            )

        return sql

    def _get_indexes_in_altered_table(self, diff):
        """
        :param diff: The table diff
        :type diff: orator.dbal.table_diff.TableDiff

        :rtype: dict
        """
        indexes = diff.from_table.get_indexes()
        column_names = self._get_column_names_in_altered_table(diff)

        for key, index in OrderedDict([(k, v) for k, v in indexes.items()]).items():
            for old_index_name, renamed_index in diff.renamed_indexes.items():
                if key.lower() == old_index_name.lower():
                    del indexes[key]

            changed = False
            index_columns = []
            for column_name in index.get_columns():
                normalized_column_name = column_name.lower()
                if normalized_column_name not in column_names:
                    del indexes[key]
                    break
                else:
                    index_columns.append(column_names[normalized_column_name])
                    if column_name != column_names[normalized_column_name]:
                        changed = True

            if changed:
                indexes[key] = Index(
                    index.get_name(),
                    index_columns,
                    index.is_unique(),
                    index.is_primary(),
                    index.get_flags(),
                )

            for index in diff.removed_indexes.values():
                index_name = index.get_name().lower()
                if index_name and index_name in indexes:
                    del indexes[index_name]

            changed_indexes = (
                list(diff.changed_indexes.values())
                + list(diff.added_indexes.values())
                + list(diff.renamed_indexes.values())
            )
            for index in changed_indexes:
                index_name = index.get_name().lower()
                if index_name:
                    indexes[index_name] = index
                else:
                    indexes[len(indexes)] = index

        return indexes

    def _get_column_names_in_altered_table(self, diff):
        """
        :param diff: The table diff
        :type diff: orator.dbal.table_diff.TableDiff

        :rtype: dict
        """
        columns = OrderedDict()

        for column_name, column in diff.from_table.get_columns().items():
            columns[column_name.lower()] = column.get_name()

        for column_name, column in diff.removed_columns.items():
            column_name = column_name.lower()
            if column_name in columns:
                del columns[column_name]

        for old_column_name, column in diff.renamed_columns.items():
            column_name = column.get_name()
            columns[old_column_name.lower()] = column_name
            columns[column_name.lower()] = column_name

        for old_column_name, column_diff in diff.changed_columns.items():
            column_name = column_diff.column.get_name()
            columns[old_column_name.lower()] = column_name
            columns[column_name.lower()] = column_name

        for column_name, column in diff.added_columns.items():
            columns[column_name.lower()] = column_name

        return columns

    def _get_foreign_keys_in_altered_table(self, diff):
        """
        :param diff: The table diff
        :type diff: orator.dbal.table_diff.TableDiff

        :rtype: dict
        """
        foreign_keys = diff.from_table.get_foreign_keys()
        column_names = self._get_column_names_in_altered_table(diff)

        for key, constraint in foreign_keys.items():
            changed = False
            local_columns = []
            for column_name in constraint.get_local_columns():
                normalized_column_name = column_name.lower()
                if normalized_column_name not in column_names:
                    del foreign_keys[key]
                    break
                else:
                    local_columns.append(column_names[normalized_column_name])
                    if column_name != column_names[normalized_column_name]:
                        changed = True

            if changed:
                foreign_keys[key] = ForeignKeyConstraint(
                    local_columns,
                    constraint.get_foreign_table_name(),
                    constraint.get_foreign_columns(),
                    constraint.get_name(),
                    constraint.get_options(),
                )

        for constraint in diff.removed_foreign_keys:
            constraint_name = constraint.get_name().lower()
            if constraint_name and constraint_name in foreign_keys:
                del foreign_keys[constraint_name]

        foreign_keys_diff = diff.changed_foreign_keys + diff.added_foreign_keys
        for constraint in foreign_keys_diff:
            constraint_name = constraint.get_name().lower()
            if constraint_name:
                foreign_keys[constraint_name] = constraint
            else:
                foreign_keys[len(foreign_keys)] = constraint

        return foreign_keys

    def _get_primary_index_in_altered_table(self, diff):
        """
        :param diff: The table diff
        :type diff: orator.dbal.table_diff.TableDiff

        :rtype: dict
        """
        primary_index = {}

        for index in self._get_indexes_in_altered_table(diff).values():
            if index.is_primary():
                primary_index = {index.get_name(): index}

        return primary_index

    def supports_foreign_key_constraints(self):
        return True

    def get_boolean_type_declaration_sql(self, column):
        return "BOOLEAN"

    def get_integer_type_declaration_sql(self, column):
        return "INTEGER" + self._get_common_integer_type_declaration_sql(column)

    def get_bigint_type_declaration_sql(self, column):
        # SQLite autoincrement is implicit for INTEGER PKs, but not for BIGINT fields.
        if not column.get("autoincrement", False):
            return self.get_integer_type_declaration_sql(column)

        return "BIGINT" + self._get_common_integer_type_declaration_sql(column)

    def get_tinyint_type_declaration_sql(self, column):
        # SQLite autoincrement is implicit for INTEGER PKs, but not for TINYINT fields.
        if not column.get("autoincrement", False):
            return self.get_integer_type_declaration_sql(column)

        return "TINYINT" + self._get_common_integer_type_declaration_sql(column)

    def get_smallint_type_declaration_sql(self, column):
        # SQLite autoincrement is implicit for INTEGER PKs, but not for SMALLINT fields.
        if not column.get("autoincrement", False):
            return self.get_integer_type_declaration_sql(column)

        return "SMALLINT" + self._get_common_integer_type_declaration_sql(column)

    def get_mediumint_type_declaration_sql(self, column):
        # SQLite autoincrement is implicit for INTEGER PKs, but not for MEDIUMINT fields.
        if not column.get("autoincrement", False):
            return self.get_integer_type_declaration_sql(column)

        return "MEDIUMINT" + self._get_common_integer_type_declaration_sql(column)

    def get_datetime_type_declaration_sql(self, column):
        return "DATETIME"

    def get_date_type_declaration_sql(self, column):
        return "DATE"

    def get_time_type_declaration_sql(self, column):
        return "TIME"

    def _get_common_integer_type_declaration_sql(self, column):
        # sqlite autoincrement is implicit for integer PKs, but not when the field is unsigned
        if not column.get("autoincrement", False):
            return ""

        if not column.get("unsigned", False):
            return " UNSIGNED"

        return ""

    def get_varchar_type_declaration_sql_snippet(self, length, fixed):
        if fixed:
            return "CHAR(%s)" % length if length else "CHAR(255)"
        else:
            return "VARCHAR(%s)" % length if length else "TEXT"

    def get_blob_type_declaration_sql(self, column):
        return "BLOB"

    def get_clob_type_declaration_sql(self, column):
        return "CLOB"

    def get_column_options(self):
        return ["pk"]

    def _get_reserved_keywords_class(self):
        return SQLiteKeywords
