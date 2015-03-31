# -*- coding: utf-8 -*-

from ..support.collection import Collection as BaseCollection


class Collection(BaseCollection):

    def model_keys(self):
        """
        Get the list of primary keys.

        :rtype: list
        """
        return map(lambda m: m.get_key(), self._items)
