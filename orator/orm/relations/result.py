# -*- coding: utf-8 -*-

from wrapt import ObjectProxy


class Result(ObjectProxy):

    _results = None
    _relation = None
    _parent = None
    _kwargs = None

    def __init__(self, result, relation, parent, **kwargs):
        """
        :param query: A Builder instance
        :type query: orm.orator.Builder

        :param parent: The parent model
        :type parent: Model
        """
        super(Result, self).__init__(result)

        self._results = result
        self._relation = relation
        self._parent = parent
        self._kwargs = kwargs

    def __call__(self, *args, **kwargs):
        return self._relation.new_instance(self._parent, **self._kwargs)
