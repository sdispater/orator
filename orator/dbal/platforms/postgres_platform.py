# -*- coding: utf-8 -*-

from .platform import Platform
from .keywords.postgresql_keywords import PostgreSQLKeywords
from ..table import Table
from ..column import Column
from ..identifier import Identifier


class PostgresPlatform(Platform):

    INTERNAL_TYPE_MAPPING = {
        "smallint": "smallint",
        "int2": "smallint",
        "serial": "integer",
        "serial4": "integer",
        "int": "integer",
        "int4": "integer",
        "integer": "integer",
        "bigserial": "bigint",
        "serial8": "bigint",
        "bigint": "bigint",
        "int8": "bigint",
        "bool": "boolean",
        "boolean": "boolean",
        "text": "text",
        "tsvector": "text",
        "varchar": "string",
        "interval": "string",
        "_varchar": "string",
        "char": "string",
        "bpchar": "string",
        "inet": "string",
        "date": "date",
        "datetime": "datetime",
        "timestamp": "datetime",
        "timestamptz": "datetimez",
        "time": "time",
        "timetz": "time",
        "float": "float",
        "float4": "float",
        "float8": "float",
        "double": "float",
        "double precision": "float",
        "real": "float",
        "decimal": "decimal",
        "money": "decimal",
        "numeric": "decimal",
        "year": "date",
        "uuid": "guid",
        "bytea": "blob",
        "json": "json",
    }

    def get_list_table_columns_sql(self, table):
        sql = """SELECT
                    a.attnum,
                    quote_ident(a.attname) AS field,
                    t.typname AS type,
                    format_type(a.atttypid, a.atttypmod) AS complete_type,
                    (SELECT t1.typname FROM pg_catalog.pg_type t1 WHERE t1.oid = t.typbasetype) AS domain_type,
                    (SELECT format_type(t2.typbasetype, t2.typtypmod) FROM
                      pg_catalog.pg_type t2 WHERE t2.typtype = 'd' AND t2.oid = a.atttypid) AS domain_complete_type,
                    a.attnotnull AS isnotnull,
                    (SELECT 't'
                     FROM pg_index
                     WHERE c.oid = pg_index.indrelid
                        AND pg_index.indkey[0] = a.attnum
                        AND pg_index.indisprimary = 't'
                    ) AS pri,
                    (SELECT pg_get_expr(adbin, adrelid)
                     FROM pg_attrdef
                     WHERE c.oid = pg_attrdef.adrelid
                        AND pg_attrdef.adnum=a.attnum
                    ) AS default,
                    (SELECT pg_description.description
                        FROM pg_description WHERE pg_description.objoid = c.oid AND a.attnum = pg_description.objsubid
                    ) AS comment
                    FROM pg_attribute a, pg_class c, pg_type t, pg_namespace n
                    WHERE %s
                        AND a.attnum > 0
                        AND a.attrelid = c.oid
                        AND a.atttypid = t.oid
                        AND n.oid = c.relnamespace
                    ORDER BY a.attnum""" % self.get_table_where_clause(
            table
        )

        return sql

    def get_list_table_indexes_sql(self, table):
        sql = """
              SELECT quote_ident(relname) as relname, pg_index.indisunique, pg_index.indisprimary,
                     pg_index.indkey, pg_index.indrelid,
                     pg_get_expr(indpred, indrelid) AS where
              FROM pg_class, pg_index
              WHERE oid IN (
                  SELECT indexrelid
                  FROM pg_index si, pg_class sc, pg_namespace sn
                  WHERE %s
                  AND sc.oid=si.indrelid AND sc.relnamespace = sn.oid
              ) AND pg_index.indexrelid = oid"""

        sql = sql % self.get_table_where_clause(table, "sc", "sn")

        return sql

    def get_list_table_foreign_keys_sql(self, table):
        return (
            "SELECT quote_ident(r.conname) as conname, "
            "pg_catalog.pg_get_constraintdef(r.oid, true) AS condef "
            "FROM pg_catalog.pg_constraint r "
            "WHERE r.conrelid = "
            "("
            "SELECT c.oid "
            "FROM pg_catalog.pg_class c, pg_catalog.pg_namespace n "
            "WHERE "
            + self.get_table_where_clause(table)
            + " AND n.oid = c.relnamespace"
            ")"
            " AND r.contype = 'f'"
        )

    def get_table_where_clause(self, table, class_alias="c", namespace_alias="n"):
        where_clause = (
            namespace_alias
            + ".nspname NOT IN ('pg_catalog', 'information_schema', 'pg_toast') AND "
        )
        if table.find(".") >= 0:
            split = table.split(".")
            schema, table = split[0], split[1]
            schema = "'%s'" % schema
        else:
            schema = (
                "ANY(string_to_array((select replace(replace(setting, '\"$user\"', user), ' ', '')"
                " from pg_catalog.pg_settings where name = 'search_path'),','))"
            )

        where_clause += "%s.relname = '%s' AND %s.nspname = %s" % (
            class_alias,
            table,
            namespace_alias,
            schema,
        )

        return where_clause

    def get_advanced_foreign_key_options_sql(self, foreign_key):
        query = ""

        if foreign_key.has_option("match"):
            query += " MATCH %s" % foreign_key.get_option("match")

        query += super(PostgresPlatform, self).get_advanced_foreign_key_options_sql(
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
        sql = []

        for column_diff in diff.changed_columns.values():
            if self.is_unchanged_binary_column(column_diff):
                continue

            old_column_name = column_diff.get_old_column_name().get_quoted_name(self)
            column = column_diff.column

            if any(
                [
                    column_diff.has_changed("type"),
                    column_diff.has_changed("precision"),
                    column_diff.has_changed("scale"),
                    column_diff.has_changed("fixed"),
                ]
            ):
                query = (
                    "ALTER "
                    + old_column_name
                    + " TYPE "
                    + self.get_sql_type_declaration(column.to_dict())
                )
                sql.append(
                    "ALTER TABLE "
                    + diff.get_name(self).get_quoted_name(self)
                    + " "
                    + query
                )

            if column_diff.has_changed("default") or column_diff.has_changed("type"):
                if column.get_default() is None:
                    default_clause = " DROP DEFAULT"
                else:
                    default_clause = " SET" + self.get_default_value_declaration_sql(
                        column.to_dict()
                    )

                query = "ALTER " + old_column_name + default_clause
                sql.append(
                    "ALTER TABLE "
                    + diff.get_name(self).get_quoted_name(self)
                    + " "
                    + query
                )

            if column_diff.has_changed("notnull"):
                op = "DROP"
                if column.get_notnull():
                    op = "SET"

                query = "ALTER " + old_column_name + " " + op + " NOT NULL"
                sql.append(
                    "ALTER TABLE "
                    + diff.get_name(self).get_quoted_name(self)
                    + " "
                    + query
                )

            if column_diff.has_changed("autoincrement"):
                if column.get_autoincrement():
                    seq_name = self.get_identity_sequence_name(
                        diff.name, old_column_name
                    )

                    sql.append("CREATE SEQUENCE " + seq_name)
                    sql.append(
                        "SELECT setval('" + seq_name + "', "
                        "(SELECT MAX(" + old_column_name + ") FROM " + diff.name + "))"
                    )
                    query = (
                        "ALTER "
                        + old_column_name
                        + " SET DEFAULT nextval('"
                        + seq_name
                        + "')"
                    )
                    sql.append(
                        "ALTER TABLE "
                        + diff.get_name(self).get_quoted_name(self)
                        + " "
                        + query
                    )
                else:
                    query = "ALTER " + old_column_name + " DROP DEFAULT"
                    sql.append(
                        "ALTER TABLE "
                        + diff.get_name(self).get_quoted_name(self)
                        + " "
                        + query
                    )

            if column_diff.has_changed("length"):
                query = (
                    "ALTER "
                    + old_column_name
                    + " TYPE "
                    + self.get_sql_type_declaration(column.to_dict())
                )
                sql.append(
                    "ALTER TABLE "
                    + diff.get_name(self).get_quoted_name(self)
                    + " "
                    + query
                )

        for old_column_name, column in diff.renamed_columns.items():
            sql.append(
                "ALTER TABLE " + diff.get_name(self).get_quoted_name(self) + " "
                "RENAME COLUMN "
                + Identifier(old_column_name).get_quoted_name(self)
                + " TO "
                + column.get_quoted_name(self)
            )

        return sql

    def is_unchanged_binary_column(self, column_diff):
        column_type = column_diff.column.get_type()

        if column_type not in ["blob", "binary"]:
            return False

        if isinstance(column_diff.from_column, Column):
            from_column = column_diff.from_column
        else:
            from_column = None

        if from_column:
            from_column_type = self.INTERNAL_TYPE_MAPPING[from_column.get_type()]

            if from_column_type in ["blob", "binary"]:
                return False

            return (
                len(
                    [
                        x
                        for x in column_diff.changed_properties
                        if x not in ["type", "length", "fixed"]
                    ]
                )
                == 0
            )

        if column_diff.has_changed("type"):
            return False

        return (
            len(
                [
                    x
                    for x in column_diff.changed_properties
                    if x not in ["length", "fixed"]
                ]
            )
            == 0
        )

    def convert_booleans(self, item):
        if isinstance(item, list):
            for i, value in enumerate(item):
                if isinstance(value, bool):
                    item[i] = str(value).lower()
        elif isinstance(item, bool):
            item = str(item).lower()

        return item

    def get_boolean_type_declaration_sql(self, column):
        return "BOOLEAN"

    def get_integer_type_declaration_sql(self, column):
        if column.get("autoincrement"):
            return "SERIAL"

        return "INT"

    def get_bigint_type_declaration_sql(self, column):
        if column.get("autoincrement"):
            return "BIGSERIAL"

        return "BIGINT"

    def get_smallint_type_declaration_sql(self, column):
        return "SMALLINT"

    def get_guid_type_declaration_sql(self, column):
        return "UUID"

    def get_datetime_type_declaration_sql(self, column):
        return "TIMESTAMP(0) WITHOUT TIME ZONE"

    def get_datetimetz_type_declaration_sql(self, column):
        return "TIMESTAMP(0) WITH TIME ZONE"

    def get_date_type_declaration_sql(self, column):
        return "DATE"

    def get_time_type_declaration_sql(self, column):
        return "TIME(0) WITHOUT TIME ZONE"

    def get_string_type_declaration_sql(self, column):
        length = column.get("length", "255")
        fixed = column.get("fixed")

        if fixed:
            return "CHAR(%s)" % length
        else:
            return "VARCHAR(%s)" % length

    def get_binary_type_declaration_sql(self, column):
        return "BYTEA"

    def get_blob_type_declaration_sql(self, column):
        return "BYTEA"

    def get_clob_type_declaration_sql(self, column):
        return "TEXT"

    def get_text_type_declaration_sql(self, column):
        return "TEXT"

    def get_json_type_declaration_sql(self, column):
        return "JSON"

    def get_decimal_type_declaration_sql(self, column):
        if "precision" not in column or not column["precision"]:
            column["precision"] = 10

        if "scale" not in column or not column["scale"]:
            column["precision"] = 0

        return "DECIMAL(%s, %s)" % (column["precision"], column["scale"])

    def get_float_type_declaration_sql(self, column):
        return "DOUBLE PRECISION"

    def supports_foreign_key_constraints(self):
        return True

    def has_native_json_type(self):
        return True

    def _get_reserved_keywords_class(self):
        return PostgreSQLKeywords
