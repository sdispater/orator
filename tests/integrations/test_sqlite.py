# -*- coding: utf-8 -*-

from .. import OratorTestCase
from . import IntegrationTestCase


class SQLiteIntegrationTestCase(IntegrationTestCase, OratorTestCase):
    @classmethod
    def get_manager_config(cls):
        return {
            "default": "sqlite",
            "sqlite": {"driver": "sqlite", "database": ":memory:"},
        }
