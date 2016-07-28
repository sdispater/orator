# -*- coding: utf-8 -*-

from orator.utils._helpers import data_get


cdef class Collection(object):

    cdef list _items

    def __init__(self, items=None):
        """
        Creates a new Collection

        :param items: The collection items
        :type items: dict or list or Collection or map

        :rtype: None
        """
        cdef list _items

        if items is None:
            _items = []
        else:
            _items = self._get_items(items)

        self._items = _items

    @property
    def items(self):
        return self._items\

    @classmethod
    def make(cls, items=None):
        """
        Create a new Collection instance if the value isn't one already

        :param items: The collection items
        :type items: dict or list or Collection

        :return: A Collection instance
        :rtype: Collection
        """
        if isinstance(items, cls):
            return items

        return cls(items)

    def avg(self, key=None):
        """
        Get the average value of a given key.

        :param key: The key to get the average for
        :type key: mixed

        :rtype: float
        """
        cdef int count

        count = self.count()

        if count:
            return self.sum(key) / count

    def count(self):
        return len(self._items)

    def _chunk(self, size):
        """
        Chunk the underlying collection.

        :param size: The chunk size
        :type size: int

        :rtype: Collection
        """
        cdef list items

        items = self._items

        return [items[i:i + size] for i in range(0, len(items), size)]

    def merge(self, items):
        """
        Merge the collection with the given items.

        :param items: The items to merge
        :type items: list or Collection

        :rtype: Collection
        """
        cdef list _items

        if isinstance(items, Collection):
            _items = items.all()
        else:
            _items = items

        if not isinstance(_items, list):
            raise ValueError('Unable to merge uncompatible types')

        self._items += _items

        return self

    def sum(self, callback=None):
        """
        Get the sum of the given values.

        :param callback: The callback
        :type callback: callable or string or None

        :rtype: mixed
        """
        if callback is None:
            return sum(self.items)

        callback = self._value_retriever(callback)

        return self.reduce(lambda result, item: (result or 0) + callback(item))

    def transform(self, callback):
        """
        Transform each item in the collection using a callback.

        :param callback: The callback
        :type callback: callable

        :rtype: Collection
        """
        self._items = self.map(callback).all()

        return self

    def unique(self, key=None):
        """
        Return only unique items from the collection list.

        :param key: The key to chech uniqueness on
        :type key: mixed

        :rtype: Collection
        """
        cdef set seen
        cdef list exists

        if key is None:
            seen = set()
            seen_add = seen.add

            return self.__class__([x for x in self.items if not (x in seen or seen_add(x))])

        key = self._value_retriever(key)

        exists = []

        def _check(item):
            id_ = key(item)
            if id_ in exists:
                return True

            exists.append(id_)

        return self.reject(_check)

    def _value_retriever(self, value):
        """
        Get a value retrieving callback.

        :type value: mixed

        :rtype: callable
        """
        if self._use_as_callable(value):
            return value

        return lambda item: data_get(item, value)

    def _set_items(self, items):
        self._items = items

    cdef list _get_items(self, items):
        if isinstance(items, list):
            return items
        elif isinstance(items, tuple):
            return list(items)
        elif isinstance(items, Collection):
            return items.all()
        elif hasattr('items', 'to_list'):
            return items.to_list()

        return [items]
