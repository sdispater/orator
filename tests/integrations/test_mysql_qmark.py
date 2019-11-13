# -*- coding: utf-8 -*-

import os

from .. import OratorTestCase
from . import IntegrationTestCase


class MySQLQmarkIntegrationTestCase(IntegrationTestCase, OratorTestCase):
    @classmethod
    def get_manager_config(cls):
        ci = os.environ.get("CI", False)

        if ci:
            database = "orator_test"
            user = "root"
            password = ""
            host = "localhost"
        else:
            database = "orator_test"
            user = "orator"
            password = "orator"
            host = "mysql-db"

        return {
            "default": "mysql",
            "mysql": {
                "driver": "mysql",
                "database": database,
                "user": user,
                "password": password,
                "use_qmark": True,
                "host": host,
            },
        }

    def get_marker(self):
        return "?"
