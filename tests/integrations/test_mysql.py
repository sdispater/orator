# -*- coding: utf-8 -*-

import os

from .. import OratorTestCase
from . import IntegrationTestCase


class MySQLIntegrationTestCase(IntegrationTestCase, OratorTestCase):
    @classmethod
    def get_manager_config(cls):
        ci = os.environ.get("CI", False)

        if ci:
            database = "orator_test"
            user = "root"
            password = ""
        else:
            database = "orator_test"
            user = "orator"
            password = "orator"

        return {
            "default": "mysql",
            "mysql": {
                "driver": "mysql",
                "database": database,
                "user": user,
                "password": password,
            },
        }

    def get_marker(self):
        return "%s"
