# -*- coding: utf-8 -*-

import re
from pendulum import Pendulum, Date

try:
    import MySQLdb as mysql

    # Fix for understanding Pendulum object
    import MySQLdb.converters

    MySQLdb.converters.conversions[Pendulum] = MySQLdb.converters.DateTime2literal
    MySQLdb.converters.conversions[Date] = MySQLdb.converters.Thing2Literal

    from MySQLdb.cursors import DictCursor as cursor_class

    keys_fix = {"password": "passwd", "database": "db"}
except ImportError as e:
    try:
        import pymysql as mysql

        # Fix for understanding Pendulum object
        import pymysql.converters

        pymysql.converters.conversions[Pendulum] = pymysql.converters.escape_datetime
        pymysql.converters.conversions[Date] = pymysql.converters.escape_date

        from pymysql.cursors import DictCursor as cursor_class

        keys_fix = {}
    except ImportError as e:
        mysql = None
        cursor_class = object

from ..dbal.platforms import MySQLPlatform, MySQL57Platform
from .connector import Connector
from ..utils.qmarker import qmark, denullify
from ..utils.helpers import serialize


class Record(dict):
    def __getattr__(self, item):
        try:
            return self[item]
        except KeyError:
            raise AttributeError(item)

    def serialize(self):
        return serialize(self)


class BaseDictCursor(cursor_class):
    def _fetch_row(self, size=1):
        # Overridden for mysqclient
        if not self._result:
            return ()
        rows = self._result.fetch_row(size, self._fetch_type)

        return tuple(Record(r) for r in rows)

    def _conv_row(self, row):
        # Overridden for pymysql
        return Record(super(BaseDictCursor, self)._conv_row(row))


class DictCursor(BaseDictCursor):
    def execute(self, query, args=None):
        query = qmark(query)

        return super(DictCursor, self).execute(query, args)

    def executemany(self, query, args):
        query = qmark(query)

        return super(DictCursor, self).executemany(query, denullify(args))


class MySQLConnector(Connector):

    RESERVED_KEYWORDS = [
        "log_queries",
        "driver",
        "prefix",
        "engine",
        "collation",
        "name",
        "use_qmark",
    ]

    SUPPORTED_PACKAGES = ["PyMySQL", "mysqlclient"]

    def _do_connect(self, config):
        config = dict(config.items())
        for key, value in keys_fix.items():
            config[value] = config[key]
            del config[key]

        config["autocommit"] = True
        config["cursorclass"] = self.get_cursor_class(config)

        return self.get_api().connect(**self.get_config(config))

    def get_default_config(self):
        return {"charset": "utf8", "use_unicode": True}

    def get_cursor_class(self, config):
        if config.get("use_qmark"):
            return DictCursor

        return BaseDictCursor

    def get_api(self):
        return mysql

    def get_server_version(self):
        version = self._connection.get_server_info()

        version_parts = re.match(
            "^(?P<major>\d+)(?:\.(?P<minor>\d+)(?:\.(?P<patch>\d+))?)?", version
        )

        major = int(version_parts.group("major"))
        minor = version_parts.group("minor") or 0
        patch = version_parts.group("patch") or 0

        minor, patch = int(minor), int(patch)

        server_version = (major, minor, patch, "")

        if "mariadb" in version.lower():
            server_version = (major, minor, patch, "mariadb")

        return server_version

    def _create_database_platform_for_version(self, version):
        major, minor, _, extra = version

        if extra == "mariadb":
            return self.get_dbal_platform()

        if (major, minor) >= (5, 7):
            return MySQL57Platform()

        return self.get_dbal_platform()

    def get_dbal_platform(self):
        return MySQLPlatform()
