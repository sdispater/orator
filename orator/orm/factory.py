# -*- coding: utf-8 -*-

import os
import inflection
from faker import Faker
from functools import wraps
from .factory_builder import FactoryBuilder


class Factory(object):
    def __init__(self, faker=None, resolver=None):
        """
        :param faker: A faker generator instance
        :type faker: faker.Generator
        """
        if faker is None:
            self._faker = Faker()
        else:
            self._faker = faker

        self._definitions = {}
        self._resolver = resolver

    @classmethod
    def construct(cls, faker, path_to_factories=None):
        """
        Create a new factory container.

        :param faker: A faker generator instance
        :type faker: faker.Generator

        :param path_to_factories: The path to factories
        :type path_to_factories: str

        :rtype: Factory
        """
        factory = faker.__class__()

        if path_to_factories is not None and os.path.isdir(path_to_factories):
            for filename in os.listdir(path_to_factories):
                if os.path.isfile(filename):
                    cls._resolve(path_to_factories, filename)

        return factory

    def define_as(self, klass, name):
        """
        Define a class with the given short name.

        :param klass: The class
        :type klass: class

        :param name: The short name
        :type name: str
        """
        return self.define(klass, name)

    def define(self, klass, name="default"):
        """
        Define a class with a given set of attributes.

        :param klass: The class
        :type klass: class

        :param name: The short name
        :type name: str
        """

        def decorate(func):
            @wraps(func)
            def wrapped(*args, **kwargs):
                return func(*args, **kwargs)

            self.register(klass, func, name=name)

            return wrapped

        return decorate

    def register(self, klass, callback, name="default"):
        """
        Register a class with a function.

        :param klass: The class
        :type klass: class

        :param callback: The callable
        :type callback: callable

        :param name: The short name
        :type name: str
        """
        if klass not in self._definitions:
            self._definitions[klass] = {}

        self._definitions[klass][name] = callback

    def register_as(self, klass, name, callback):
        """
        Register a class with a function.

        :param klass: The class
        :type klass: class

        :param callback: The callable
        :type callback: callable

        :param name: The short name
        :type name: str
        """
        return self.register(klass, callback, name)

    def create(self, klass, **attributes):
        """
        Create an instance of the given model and persist it to the database.

        :param klass: The class
        :type klass: class

        :param attributes: The instance attributes
        :type attributes: dict

        :return: mixed
        """
        return self.of(klass).create(**attributes)

    def create_as(self, klass, name, **attributes):
        """
        Create an instance of the given model and type and persist it to the database.

        :param klass: The class
        :type klass: class

        :param name: The type
        :type name: str

        :param attributes: The instance attributes
        :type attributes: dict

        :return: mixed
        """
        return self.of(klass, name).create(**attributes)

    def make(self, klass, **attributes):
        """
        Create an instance of the given model.

        :param klass: The class
        :type klass: class

        :param attributes: The instance attributes
        :type attributes: dict

        :return: mixed
        """
        return self.of(klass).make(**attributes)

    def make_as(self, klass, name, **attributes):
        """
        Create an instance of the given model and type.

        :param klass: The class
        :type klass: class

        :param name: The type
        :type name: str

        :param attributes: The instance attributes
        :type attributes: dict

        :return: mixed
        """
        return self.of(klass, name).make(**attributes)

    def raw_of(self, klass, name, **attributes):
        """
        Get the raw attribute dict for a given named model.

        :param klass: The class
        :type klass: class

        :param name: The type
        :type name: str

        :param attributes: The instance attributes
        :type attributes: dict

        :return: dict
        """
        return self.raw(klass, _name=name, **attributes)

    def raw(self, klass, _name="default", **attributes):
        """
        Get the raw attribute dict for a given named model.

        :param klass: The class
        :type klass: class

        :param _name: The type
        :type _name: str

        :param attributes: The instance attributes
        :type attributes: dict

        :return: dict
        """
        raw = self._definitions[klass][_name](self._faker)

        raw.update(attributes)

        return raw

    def of(self, klass, name="default"):
        """
        Create a builder for the given model.

        :param klass: The class
        :type klass: class

        :param name: The type
        :type name: str

        :return: orator.orm.factory_builder.FactoryBuilder
        """
        return FactoryBuilder(
            klass, name, self._definitions, self._faker, self._resolver
        )

    def build(self, klass, name="default", amount=None):
        """
        Makes a factory builder with a specified amount.

        :param klass: The class
        :type klass: class

        :param name: The type
        :type name: str

        :param amount: The number of models to create
        :type amount: int

        :return: mixed
        """
        if amount is None:
            if isinstance(name, int):
                amount = name
                name = "default"
            else:
                amount = 1

        return self.of(klass, name).times(amount)

    @classmethod
    def _resolve(cls, path, factory_file):
        """
        Resolve a migration instance from a file.

        :param path: The path to factories directory
        :type path: str

        :param factory_file: The migration file
        :type factory_file: str

        :rtype: Factory
        """
        variables = {}

        name = factory_file
        factory_file = os.path.join(path, factory_file)

        with open(factory_file) as fh:
            exec(fh.read(), {}, variables)

        klass = variables[inflection.camelize(name)]

        instance = klass()

        return instance

    def set_connection_resolver(self, resolver):
        self._resolver = resolver

    def __getitem__(self, item):
        return self.make(item)

    def __setitem__(self, key, value):
        return self.define(key, value)

    def __contains__(self, item):
        return item in self._definitions

    def __call__(self, klass, name="default", amount=None):
        """
        Makes a factory builder with a specified amount.

        :param klass: The class
        :type klass: class

        :param name: The type
        :type name: str

        :param amount: The number of models to create
        :type amount: int

        :return: mixed
        """
        return self.build(klass, name, amount)
