# -*- coding: utf-8 -*-

from .sqlite_platform import SQLitePlatform
from .mysql_platform import MySQLPlatform
from .mysql57_platform import MySQL57Platform
from .postgres_platform import PostgresPlatform

PLATFORMS = {
    'sqlite': {
        'default': SQLitePlatform
    },
    'mysql': {
        '5.7': MySQL57Platform,
        'default': MySQLPlatform
    },
    'pgsql': {
        'default': PostgresPlatform
    }
}
