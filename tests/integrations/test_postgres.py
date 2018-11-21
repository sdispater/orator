# -*- coding: utf-8 -*-

import os

from .. import OratorTestCase
from . import IntegrationTestCase


class PostgresIntegrationTestCase(IntegrationTestCase, OratorTestCase):
    @classmethod
    def get_manager_config(cls):
        ci = os.environ.get("CI", False)

        if ci:
            database = "orator_test"
            user = "postgres"
            password = None
        else:
            database = "orator_test"
            user = "orator"
            password = "orator"

        return {
            "default": "postgres",
            "postgres": {
                "driver": "pgsql",
                "database": database,
                "user": user,
                "password": password,
            },
        }

    def get_marker(self):
        return "%s"
