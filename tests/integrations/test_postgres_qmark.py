# -*- coding: utf-8 -*-

import os

from .. import OratorTestCase
from . import IntegrationTestCase


class PostgresQmarkIntegrationTestCase(IntegrationTestCase, OratorTestCase):
    @classmethod
    def get_manager_config(cls):
        ci = os.environ.get("CI", False)

        if ci:
            database = "orator_test"
            user = "postgres"
            password = None
            host = "localhost"
        else:
            database = "orator_test"
            user = "orator"
            password = "orator"
            host = "postgres-db"

        return {
            "default": "postgres",
            "postgres": {
                "driver": "pgsql",
                "database": database,
                "user": user,
                "password": password,
                "use_qmark": True,
                "host": host,
            },
        }

    def get_marker(self):
        return "?"
