# -*- coding: utf-8 -*-

from ..support.collection import Collection as BaseCollection


class Collection(BaseCollection):

    def load(self, *relations):
        """
        Load a set of relationships onto the collection.
        """
        if len(self.items) > 0:
            query = self.first().new_query().with_(*relations)

            self._set_items(query.eager_load_relations(self.items))

        return self

    def lists(self, value, key=None):
        """
        Get a list with the values of a given key

        :rtype: list
        """
        results = map(lambda x: getattr(x, value), self.items)

        return list(results)

    def model_keys(self):
        """
        Get the list of primary keys.

        :rtype: list
        """
        return map(lambda m: m.get_key(), self.items)
