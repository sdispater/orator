# -*- coding: utf-8 -*-

from .collection import Collection


class FactoryBuilder(object):
    def __init__(self, klass, name, definitions, faker, resolver=None):
        """
        :param klass: The class
        :type klass: class

        :param name: The type
        :type name: str

        :param definitions: The factory definitions
        :type definitions: dict

        :param faker: The faker generator instance
        :type faker: faker.Generator
        """
        self._name = name
        self._klass = klass
        self._faker = faker
        self._definitions = definitions
        self._amount = 1
        self._resolver = resolver

    def times(self, amount):
        """
        Set the amount of models to create / make

        :param amount: The amount of models
        :type amount: int

        :rtype: FactoryBuilder
        """
        self._amount = amount

        return self

    def create(self, **attributes):
        """
        Create a collection of models and persist them to the database.

        :param attributes: The models attributes
        :type attributes: dict

        :return: mixed
        """
        results = self.make(**attributes)

        if self._amount == 1:
            if self._resolver:
                results.set_connection_resolver(self._resolver)

            results.save()
        else:
            if self._resolver:
                results.each(lambda r: r.set_connection_resolver(self._resolver))

            for result in results:
                result.save()

        return results

    def make(self, **attributes):
        """
        Create a collection of models.

        :param attributes: The models attributes
        :type attributes: dict

        :return: mixed
        """
        if self._amount == 1:
            return self._make_instance(**attributes)
        else:
            results = []

            for _ in range(self._amount):
                results.append(self._make_instance(**attributes))

            return Collection(results)

    def _make_instance(self, **attributes):
        """
        Make an instance of the model with the given attributes.

        :param attributes: The models attributes
        :type attributes: dict

        :return: mixed
        """
        definition = self._definitions[self._klass][self._name](self._faker)
        definition.update(attributes)

        instance = self._klass()
        instance.force_fill(**definition)

        return instance

    def set_connection_resolver(self, resolver):
        self._resolver = resolver
