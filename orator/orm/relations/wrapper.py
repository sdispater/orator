# -*- coding: utf-8 -*-

from lazy_object_proxy import Proxy
from functools import wraps


def wrapped(func):
    @wraps(func)
    def _wrapper(*args, **kwargs):
        return Wrapper(func(*args, **kwargs))

    return _wrapper


class Wrapper(Proxy):
    """
    Wrapper around a relation which provide
    dynamic property functionality.
    """

    _relation = None

    def __init__(self, relation):
        """
        :param relation: The underlying relation.
        :type relation: Relation
        :return:
        """
        super(Wrapper, self).__init__(self._get_results)

        self._relation = relation

    def _get_results(self):
        return self._relation.get_results()

    def __call__(self, *args, **kwargs):
        return self._relation.new_instance(self._relation.get_parent())

    def __repr__(self):
        return repr(self.__wrapped__)


class BelongsToManyWrapper(Wrapper):

    def with_timestamps(self):
        self._relation.with_timestamps()

        return self

    def with_pivot(self, *columns):
        self._relation.with_pivot(*columns)

        return self
