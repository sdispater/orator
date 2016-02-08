# -*- coding: utf-8 -*-

from __future__ import division


import simplejson as json
from copy import copy

from ..utils import reduce, basestring, value, data_get, deprecated


class CollectionError(Exception):

    pass


class Collection(object):

    def __init__(self, items=None):
        """
        Creates a new Collection

        :param items: The collection items
        :type items: dict or list or Collection or map

        :rtype: None
        """
        if items is None:
            items = []
        else:
            items = self._get_items(items)

        if not isinstance(items, (list, dict, tuple)):
            self._items = [items]
        else:
            self._items = items

    @property
    def items(self):
        return self._items

    @classmethod
    def make(cls, items=None):
        """
        Create a new Collection instance if the value isn't one already

        :param items: The collection items
        :type items: dict or list or Collection

        :return: A Collection instance
        :rtype: Collection
        """
        if isinstance(items, Collection):
            return items

        return cls(items)

    def all(self):
        """
        Get all of the items in the collection.

        :return: The items in the collections
        :type: mixed
        """
        return self.items

    def avg(self, key=None):
        """
        Get the average value of a given key.

        :param key: The key to get the average for
        :type key: mixed

        :rtype: float or int
        """
        count = self.count()

        if count:
            return self.sum(key) / count

    def chunk(self, size, preserve_keys=False):
        """
        Chunk the underlying collection.

        :param size: The chunk size
        :type size: int

        :param preserve_keys: Preserve the dictionary keys
        :type preserve_keys: bool

        :rtype: Collection
        """
        if isinstance(self.items, dict):
            if not preserve_keys:
                items = list(self.items.values())
            else:
                chunks = []
                chunk = {}
                for i, key in enumerate(self.items.keys()):
                    if i != 0 and i % size == 0:
                        chunks.append(chunk)
                        chunk = {}

                    chunk[key] = self.items[key]

                return self.__class__(list(map(Collection, chunks)))
        else:
            items = self.items

        chunks = [items[i:i + size] for i in range(0, len(items), size)]

        return self.__class__(list(map(Collection, chunks)))

    def collapse(self):
        """
        Collapse the collection items into a single element (dict or list)

        :return: A new Collection instance with collapsed items
        :rtype: Collection
        """
        results = []

        if isinstance(self._items, dict):
            items = self.items.values()
        else:
            items = self.items

        for values in items:
            if isinstance(values, Collection):
                values = values.all()

            results += values

        return self.__class__(results)

    def contains(self, key, value=None):
        """
        Determine if an element is in the collection

        :param key: The element
        :type key: int or str or callable

        :param value: The value of the element
        :type value: mixed

        :return: Whether the element is in the collection
        :rtype: bool
        """
        if value is not None:
            return self.contains(lambda x: data_get(x, key) == value)

        if self._use_as_callable(key):
            return self.first(key) is not None

        return key in self.items

    def __contains__(self, item):
        return self.contains(item)

    def count(self):
        return len(self.items)

    def diff(self, items):
        """
        Diff the collections with the given items

        :param items: The items to diff with
        :type items: mixed

        :return: A Collection instance
        :rtype: Collection
        """
        if isinstance(self.items, dict):
            elements = {}
            for key, val in self.items.items():
                if key not in items:
                    elements[key] = val
                elif items[key] != val:
                    elements[key] = val

            return self.__class__(elements)
        else:
            return self.__class__([i for i in self.items if i not in items])

    def each(self, callback):
        """
        Execute a callback over each item.

        .. code::

            collection = Collection([1, 2, 3])
            collection.each(lambda x: x + 3)

        .. warning::

            It only applies the callback but does not modify the collection's items.
            Use the `transform() <#orator.support.Collection.transform>`_ method to
            modify the collection.

        :param callback: The callback to execute
        :type callback: callable

        :rtype: Collection
        """
        if isinstance(self.items, dict):
            items = self.items.values()
        else:
            items = self.items

        for item in items:
            if callback(item) is False:
                break

        return self

    def every(self, step, offset=0):
        """
        Create a new collection consisting of every n-th element.

        :param step: The step size
        :type step: int

        :param offset: The start offset
        :type offset: int

        :rtype: Collection
        """
        new = []

        for position, item in enumerate(self.items):
            if position % step == offset:
                new.append(item)

        return self.__class__(new)

    def without(self, *keys):
        """
        Get all items except for those with the specified keys.

        :param keys: The keys to remove
        :type keys: tuple

        :rtype: Collection
        """
        items = copy(self.items)

        if not isinstance(items, dict):
            keys = reversed(sorted(keys))

        for key in keys:
            del items[key]

        return self.__class__(items)

    def only(self, *keys):
        """
        Get the items with the specified keys.

        :param keys: The keys to keep
        :type keys: tuple

        :rtype: Collection
        """
        if isinstance(self.items, dict):
            items = {}

            for key, value in self.items.items():
                if key in keys:
                    items[key] = value
        else:
            items = []

            for key, value in enumerate(self.items):
                if key in keys:
                    items.append(value)

        return self.__class__(items)

    def filter(self, callback=None):
        """
        Run a filter over each of the items.

        :param callback: The filter callback
        :type callback: callable or None

        :rtype: Collection
        """
        if callback:
            return self.__class__(list(filter(callback, self.items)))

        return self.__class__(list(filter(None, self.items)))

    def where(self, key, value):
        """
        Filter items by the given key value pair.

        :param key: The key to filter by
        :type key: str

        :param value: The value to filter by
        :type value: mixed

        :rtype: Collection
        """
        return self.filter(lambda item: data_get(item, key) == value)

    def first(self, callback=None, default=None):
        """
        Get the first item of the collection.

        :param default: The default value
        :type default: mixed
        """
        if isinstance(self.items, dict):
            raise CollectionError('first() method cannot be used on dictionary items')

        if callback is not None:
            for val in self.items:
                if callback(val):
                    return val

            return value(default)

        if len(self.items) > 0:
            return self.items[0]
        else:
            return default

    def flatten(self):
        """
        Get a flattened list of the items in the collection.

        :rtype: Collection
        """
        def _flatten(d):
            if isinstance(d, dict):
                for v in d.values():
                    for nested_v in _flatten(v):
                        yield nested_v
            elif isinstance(d, list):
                for list_v in d:
                    for nested_v in _flatten(list_v):
                        yield nested_v
            else:
                yield d

        return Collection(list(_flatten(self.items)))

    def flip(self):
        """
        Flip the items in the collection.

        :rtype: Collection
        """
        if isinstance(self.items, dict):
            items = dict(zip(self.items.values(), self.items.keys()))
        else:
            items = self.items

        return self.__class__(items)

    def forget(self, *keys):
        """
        Remove an item from the collection by key.

        :param keys: The keys to remove
        :type keys: tuple

        :rtype: Collection
        """
        if not isinstance(self.items, dict):
            keys = reversed(sorted(keys))

        for key in keys:
            del self[key]

        return self

    def get(self, key, default=None):
        """
        Get an element of the collection.

        :param key: The index of the element
        :type key: mixed

        :param default: The default value to return
        :type default: mixed

        :rtype: mixed
        """
        if isinstance(self.items, dict):
            if key in self:
                return self[key]

            return value(default)

        try:
            return self.items[key]
        except IndexError:
            return value(default)

    def implode(self, value, glue=''):
        """
        Concatenate values of a given key as a string.

        :param value: The value
        :type value: str

        :param glue: The glue
        :type glue: str

        :rtype: str
        """
        first = self.first()

        if not isinstance(first, (basestring)):
            return glue.join(self.pluck(value).all())

        return value.join(self.items)

    def last(self, callback=None, default=None):
        """
        Get the last item of the collection.

        :param default: The default value
        :type default: mixed
        """
        if isinstance(self.items, dict):
            raise CollectionError('last() method cannot be used on dictionary items')

        if callback is not None:
            for val in reversed(self.items):
                if callback(val):
                    return val

            return value(default)

        if len(self.items) > 0:
            return self.items[-1]
        else:
            return default

    def pluck(self, value, key=None):
        """
        Get a list with the values of a given key.

        :rtype: Collection
        """
        if key:
            results = dict(map(lambda x: (data_get(x, key), data_get(x, value)), self.items))
        else:
            results = list(map(lambda x: data_get(x, value), self.items))

        return self.__class__(results)

    def lists(self, value, key=None):
        """
        Alias for "pluck"

        :rtype: list
        """
        return self.pluck(value, key)

    def map(self, callback):
        """
        Run a map over each of the item.

        :param callback: The map function
        :type callback: callable

        :rtype: Collection
        """
        if isinstance(self.items, dict):
            return self.__class__(list(map(callback, self.items.values())))

        return self.__class__(list(map(callback, self.items)))

    def max(self, key=None):
        """
        Get the max value of a given key.

        :param key: The key
        :type key: str or None

        :rtype: mixed
        """
        def _max(result, item):
            val = data_get(item, key)

            if result is None or val > result:
                return value

            return result

        return self.reduce(_max)

    def min(self, key=None):
        """
        Get the min value of a given key.

        :param key: The key
        :type key: str or None

        :rtype: mixed
        """
        def _min(result, item):
            val = data_get(item, key)

            if result is None or val < result:
                return value

            return result

        return self.reduce(_min)

    def merge(self, items):
        """
        Merge the collection with the given items.

        :param items: The items to merge
        :type items: list or dict or Collection

        :rtype: Collection
        """
        if isinstance(items, Collection):
            items = items.all()

        if isinstance(self.items, dict) and not isinstance(items, dict) \
                or isinstance(self.items, list) and not isinstance(items, list):
            raise CollectionError('Unable to merge uncompatible types')

        if isinstance(self.items, dict):
            self.items.update(items)
        else:
            self._items += items

        return self

    def for_page(self, page, per_page):
        """
        "Paginate" the collection by slicing it into a smaller collection.

        :param page: The current page
        :type page: int

        :param per_page: Number of items by slice
        :type per_page: int

        :rtype: Collection
        """
        start = (page - 1) * per_page
        return self[start:start + per_page]

    def pop(self, key=None):
        """
        Remove the item at the given index, and return it.
        If no index is specified, returns the last item.

        :param key: The index of the item to return
        :type key: mixed

        :rtype: mixed
        """
        if isinstance(self.items, dict):
            value = self.items[key]

            del self.items[key]

            return value

        if key is None:
            key = -1

        return self.items.pop(key)

    def prepend(self, value):
        """
        Push an item onto the beginning of the collection.

        :param value: The value to push
        :type value: mixed

        :rtype: Collection
        """
        if isinstance(self.items, dict):
            return self

        self.items.insert(0, value)

        return self

    def append(self, value):
        """
        Push an item onto the end of the collection.

        :param value: The value to push
        :type value: mixed

        :rtype: Collection
        """
        if isinstance(self.items, dict):
            return self

        self.items.append(value)

        return self

    def push(self, value):
        """
        Alias for append.

        :param value: The value to push
        :type value: mixed

        :rtype: Collection
        """
        return self.append(value)

    def pull(self, key, default=None):
        """
        Pulls an item from the collection.

        :param key: The key
        :type key: mixed

        :param default: The default value
        :type default: mixed

        :rtype: mixed
        """
        val = self.get(key, default)

        self.forget(key)

        return val

    def put(self, key, value):
        """
        Put an item in the collection by key.

        :param key: The key
        :type key: mixed

        :param value: The value
        :type value: mixed

        :rtype: Collection
        """
        self[key] = value

        return self

    def reduce(self, callback, initial=None):
        """
        Reduce the collection to a single value.

        :param callback: The callback
        :type callback: callable

        :param initial: The initial value
        :type initial: mixed

        :rtype: mixed
        """
        return reduce(callback, self.items, initial)

    def reject(self, callback):
        """
        Create a collection of all elements that do not pass a given truth test.

        :param callback: The truth test
        :type callback: callable

        :rtype: Collection
        """
        if self._use_as_callable(callback):
            return self.filter(lambda item: not callback(item))

        return self.filter(lambda item: item != callback)

    def reverse(self):
        """
        Reverse items order.

        :rtype: Collection
        """
        if isinstance(self.items, dict):
            return self

        return self.__class__(list(reversed(self.items)))

    def shift(self):
        """
        Remove first item of the collection, and return it.

        :rtype: mixed
        """
        return self.pop(0)

    def sort(self, callback=None):
        """
        Sort through each item with a callback.

        :param callback: The callback
        :type callback: callable or None

        :rtype: Collection
        """
        items = self.items

        if callback:
            return self.__class__(sorted(items, key=callback))
        else:
            return self.__class__(sorted(items))

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

    def take(self, limit):
        """
        Take the first or last n items.

        :param limit: The number of items to take
        :type limit: int

        :rtype: Collection
        """
        if limit < 0:
            return self[limit:]

        return self[:limit]

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

    def values(self):
        """
        Return collection values.

        :rtype: Collection
        """
        if not isinstance(self.items, dict):
            return self

        return self.__class__(list(self.items.values()))

    def keys(self):
        """
        Return collection keys.

        :rtype: Collection
        """
        if not isinstance(self.items, dict):
            return self

        return self.__class__(list(self.items.keys()))

    def zip(self, *items):
        """
        Zip the collection together with one or more arrays.

        :param items: The items to zip
        :type items: list

        :rtype: Collection
        """
        return self.__class__(list(zip(self.items, *items)))

    def is_empty(self):
        return len(self) == 0

    def _get_items(self, items):
        if isinstance(items, Collection):
            items = items.all()
        elif hasattr('items', 'to_list'):
            items = items.to_list()
        elif hasattr('items', 'to_dict'):
            items = items.to_dict()

        return items

    def _value_retriever(self, value):
        """
        Get a value retrieving callback.

        :type value: mixed

        :rtype: callable
        """
        if self._use_as_callable(value):
            return value

        return lambda item: data_get(item, value)

    def _use_as_callable(self, value):
        """
        Determine if the given value is callable.

        :type value: mixed

        :rtype: bool
        """
        return not isinstance(value, basestring) and callable(value)

    @deprecated
    def to_dict(self):
        return self.serialize()

    def serialize(self):
        """
        Get the collection of items as a serialized object (ready to be json encoded).

        :rtype: dict or list
        """
        def _serialize(value):
            if hasattr(value, 'serialize'):
                return value.serialize()
            elif hasattr(value, 'to_dict'):
                return value.to_dict()
            else:
                return value

        if not isinstance(self.items, dict):
            return list(map(_serialize, self.items))

        items = {}
        for key, value in self.items.items():
            items[key] = _serialize(value)

        return items

    def to_json(self, **options):
        """
        Get the collection of items as JSON.

        :param options: JSON encoding options:
        :type options: dict

        :rtype: str
        """
        return json.dumps(self.serialize(), **options)

    def __len__(self):
        return len(self.items)

    def __iter__(self):
        for item in self.items:
            yield item

    def __getitem__(self, item):
        if isinstance(item, slice):
            return self.__class__.make(self.items[item])

        return self.items[item]

    def __setitem__(self, key, value):
        self.items[key] = value

    def __delitem__(self, key):
        del self.items[key]
