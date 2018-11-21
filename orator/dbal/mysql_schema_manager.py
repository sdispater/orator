# -*- coding: utf-8 -*-

import re
from collections import OrderedDict
from .column import Column
from .foreign_key_constraint import ForeignKeyConstraint
from .schema_manager import SchemaManager
from .platforms.mysql_platform import MySQLPlatform


class MySQLSchemaManager(SchemaManager):
    def _get_portable_table_column_definition(self, table_column):
        db_type = table_column["type"].lower()
        type_match = re.match("(.+)\((.*)\).*", db_type)
        if type_match:
            db_type = type_match.group(1)

        if "length" in table_column:
            length = table_column["length"]
        else:
            if type_match and type_match.group(2) and "," not in type_match.group(2):
                length = int(type_match.group(2))
            else:
                length = 0

        fixed = None

        if "name" not in table_column:
            table_column["name"] = ""

        precision = None
        scale = None
        extra = {}

        type = self._platform.get_type_mapping(db_type)

        if db_type in ["char", "binary"]:
            fixed = True
        elif db_type in ["float", "double", "real", "decimal", "numeric"]:
            match = re.match("([A-Za-z]+\(([0-9]+),([0-9]+)\))", table_column["type"])
            if match:
                precision = match.group(1)
                scale = match.group(2)
                length = None
        elif db_type == "tinytext":
            length = MySQLPlatform.LENGTH_LIMIT_TINYTEXT
        elif db_type == "text":
            length = MySQLPlatform.LENGTH_LIMIT_TEXT
        elif db_type == "mediumtext":
            length = MySQLPlatform.LENGTH_LIMIT_MEDIUMTEXT
        elif db_type == "tinyblob":
            length = MySQLPlatform.LENGTH_LIMIT_TINYBLOB
        elif db_type == "blob":
            length = MySQLPlatform.LENGTH_LIMIT_BLOB
        elif db_type == "mediumblob":
            length = MySQLPlatform.LENGTH_LIMIT_MEDIUMBLOB
        elif db_type in ["tinyint", "smallint", "mediumint", "int", "bigint", "year"]:
            length = None
        elif db_type == "enum":
            length = None
            extra["definition"] = "({})".format(type_match.group(2))

        if length is None or length == 0:
            length = None

        options = {
            "length": length,
            "unsigned": table_column["type"].find("unsigned") != -1,
            "fixed": fixed,
            "notnull": table_column["null"] != "YES",
            "default": table_column.get("default"),
            "precision": None,
            "scale": None,
            "autoincrement": table_column["extra"].find("auto_increment") != -1,
            "extra": extra,
        }

        if scale is not None and precision is not None:
            options["scale"] = scale
            options["precision"] = precision

        column = Column(table_column["field"], type, options)

        if "collation" in table_column:
            column.set_platform_option("collation", table_column["collation"])

        return column

    def _get_portable_table_indexes_list(self, table_indexes, table_name):
        new = []
        for v in table_indexes:
            v = dict((k.lower(), value) for k, value in v.items())
            if v["key_name"] == "PRIMARY":
                v["primary"] = True
            else:
                v["primary"] = False

            if "FULLTEXT" in v["index_type"]:
                v["flags"] = {"FULLTEXT": True}
            else:
                v["flags"] = {"SPATIAL": True}

            new.append(v)

        return super(MySQLSchemaManager, self)._get_portable_table_indexes_list(
            new, table_name
        )

    def _get_portable_table_foreign_keys_list(self, table_foreign_keys):
        foreign_keys = OrderedDict()

        for value in table_foreign_keys:
            value = dict((k.lower(), v) for k, v in value.items())
            name = value.get("constraint_name", "")

            if name not in foreign_keys:
                if "delete_rule" not in value or value["delete_rule"] == "RESTRICT":
                    value["delete_rule"] = ""

                if "update_rule" not in value or value["update_rule"] == "RESTRICT":
                    value["update_rule"] = ""

                foreign_keys[name] = {
                    "name": name,
                    "local": [],
                    "foreign": [],
                    "foreign_table": value["referenced_table_name"],
                    "on_delete": value["delete_rule"],
                    "on_update": value["update_rule"],
                }

            foreign_keys[name]["local"].append(value["column_name"])
            foreign_keys[name]["foreign"].append(value["referenced_column_name"])

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
                    },
                )
            )

        return result
