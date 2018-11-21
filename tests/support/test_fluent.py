# -*- coding: utf-8 -*-

from .. import OratorTestCase
from orator.support.fluent import Fluent


class FluentTestCase(OratorTestCase):
    def test_get_method_return_attributes(self):
        fluent = Fluent(name="john")

        self.assertEqual("john", fluent.get("name"))
        self.assertEqual("default", fluent.get("foo", "default"))
        self.assertEqual("john", fluent.name)
        self.assertEqual(None, fluent.foo)

    def test_set_attributes(self):
        fluent = Fluent()

        fluent.name = "john"
        fluent.developer()
        fluent.age(25)

        self.assertEqual("john", fluent.name)
        self.assertTrue(fluent.developer)
        self.assertEqual(25, fluent.age)

        self.assertEqual(
            {"name": "john", "developer": True, "age": 25}, fluent.get_attributes()
        )

    def test_chained_attributes(self):
        fluent = Fluent()
        fluent.unsigned = False

        fluent.integer("status").unsigned()

        self.assertEqual("status", fluent.integer)
        self.assertTrue(fluent.unsigned)
