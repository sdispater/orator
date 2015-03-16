# -*- coding: utf-8 -*-


class Collection(object):

    def __init__(self, items=None):
        """
        Creates a new Collection

        :param items: The collection items
        :type items: dict or list or Collection

        :rtype: None
        """
        if items is None:
            items = []
        else:
            items = self._get_items(items)

        if not isinstance(items, (list, dict)):
            self._items = [items]
        else:
            self._items = items

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
        Get all of the items in the collection

        :return: The items in the collections
        :type: mixed
        """
        return self._items

    def collapse(self):
        """
        Collapse the collection items into a single element (dict or list)

        :return: A new Collection instance with collapsed items
        :rtype: Collection
        """
        results = []

        if isinstance(self._items, dict):
            items = self._items.values()

        for values in items:
            if isinstance(values, Collection):
                values = values.all()

            results += values

        return Collection(results)

    def contains(self, key, value=None):
        """
        Determine if an element is in the collection

        :param key: The element
        :type key: int or str

        :param value: The value of the element
        :type value: mixed

        :return: Whether the element is in the collection
        :rtype: bool
        """
        if value is not None:
            if isinstance(self._items, list):
                return key in self._items and self._items[self._items.index(key)] == value

            return self._items.get(key) == value

        return key in self._items

    def __contains__(self, item):
        return self.contains(item)

    def diff(self, items):
        """
        Diff the collections with the given items

        :param items: The items to diff with
        :type items: mixed

        :return: A Collection instance
        :rtype: Collection
        """
        pass



    def _get_items(self, items):
        if isinstance(items, Collection):
            items = items.all()
        elif hasattr('items', 'to_list'):
            items = items.to_list()
        elif hasattr('items', 'to_dict'):
            items = items.to_dict()

        return items
