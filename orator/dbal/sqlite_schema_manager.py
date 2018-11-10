# -*- coding: utf-8 -*-

import re
from collections import OrderedDict
from .schema_manager import SchemaManager
from .column import Column
from .foreign_key_constraint import ForeignKeyConstraint


class SQLiteSchemaManager(SchemaManager):
    def _get_portable_table_column_definition(self, table_column):
        parts = table_column["type"].split("(")
        table_column["type"] = parts[0]
        if len(parts) > 1:
            length = parts[1].strip(")")
            table_column["length"] = length

        db_type = table_column["type"].lower()
        length = table_column.get("length", None)
        unsigned = False

        if " unsigned" in db_type:
            db_type = db_type.replace(" unsigned", "")
            unsigned = True

        fixed = False

        type = self._platform.get_type_mapping(db_type)
        default = table_column["dflt_value"]
        if default == "NULL":
            default = None

        if default is not None:
            # SQLite returns strings wrapped in single quotes, so we need to strip them
            default = re.sub("^'(.*)'$", "\\1", default)

        notnull = bool(table_column["notnull"])

        if "name" not in table_column:
            table_column["name"] = ""

        precision = None
        scale = None

        if db_type in ["char"]:
            fixed = True
        elif db_type in ["varchar"]:
            length = length or 255
        elif db_type in ["float", "double", "real", "decimal", "numeric"]:
            if "length" in table_column:
                if "," not in table_column["length"]:
                    table_column["length"] += ",0"

                precision, scale = tuple(
                    map(lambda x: x.strip(), table_column["length"].split(","))
                )

            length = None

        options = {
            "length": length,
            "unsigned": bool(unsigned),
            "fixed": fixed,
            "notnull": notnull,
            "default": default,
            "precision": precision,
            "scale": scale,
            "autoincrement": False,
        }

        column = Column(table_column["name"], type, options)
        column.set_platform_option("pk", table_column["pk"])

        return column

    def _get_portable_table_indexes_list(self, table_indexes, table_name):
        index_buffer = []

        # Fetch primary
        info = self._connection.select("PRAGMA TABLE_INFO (%s)" % table_name)

        for row in info:
            if row["pk"] != 0:
                index_buffer.append(
                    {
                        "key_name": "primary",
                        "primary": True,
                        "non_unique": False,
                        "column_name": row["name"],
                    }
                )

        # Fetch regular indexes
        for index in table_indexes:
            # Ignore indexes with reserved names, e.g. autoindexes
            if index["name"].find("sqlite_") == -1:
                key_name = index["name"]
                idx = {
                    "key_name": key_name,
                    "primary": False,
                    "non_unique": not bool(index["unique"]),
                }

                info = self._connection.select("PRAGMA INDEX_INFO ('%s')" % key_name)
                for row in info:
                    idx["column_name"] = row["name"]
                    index_buffer.append(idx)

        return super(SQLiteSchemaManager, self)._get_portable_table_indexes_list(
            index_buffer, table_name
        )

    def _get_portable_table_foreign_keys_list(self, table_foreign_keys):
        foreign_keys = OrderedDict()

        for value in table_foreign_keys:
            value = dict((k.lower(), v) for k, v in value.items())
            name = value.get("constraint_name", None)

            if name is None:
                name = "%s_%s_%s" % (value["from"], value["table"], value["to"])

            if name not in foreign_keys:
                if "on_delete" not in value or value["on_delete"] == "RESTRICT":
                    value["on_delete"] = None

                if "on_update" not in value or value["on_update"] == "RESTRICT":
                    value["on_update"] = None

                foreign_keys[name] = {
                    "name": name,
                    "local": [],
                    "foreign": [],
                    "foreign_table": value["table"],
                    "on_delete": value["on_delete"],
                    "on_update": value["on_update"],
                    "deferrable": value.get("deferrable", False),
                    "deferred": value.get("deferred", False),
                }

            foreign_keys[name]["local"].append(value["from"])
            foreign_keys[name]["foreign"].append(value["to"])

        result = []
        for constraint in foreign_keys.values():
            result.append(
                ForeignKeyConstraint(
                    constraint["local"],
                    constraint["foreign_table"],
                    constraint["foreign"],
                    constraint["name"],
                    {
                        "on_delete": constraint["on_delete"],
                        "on_update": constraint["on_update"],
                        "deferrable": constraint["deferrable"],
                        "deferred": constraint["deferred"],
                    },
                )
            )

        return result
