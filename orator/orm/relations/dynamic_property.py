# -*- coding: utf-8 -*-


class DynamicProperty(object):
    """
    Relationship dynamic property.

    It provides a simple way to access a property as is, returning the results,
    or has a method whihch will start a query on the relation.

    Example:

    >>> user = User.find(1)
    >>> user.roles  # will return the roles associated with the user
    >>> user.roles().first() # Will return the first role
    """

    def __init__(self, results_getter, relation):
        self._results_getter = results_getter
        self._results = None
        self._relation = relation

    def refresh(self):
        self._results = self._results_getter()

        return self._results

    @property
    def instance(self):
        if not self._results:
            self._results = self._results_getter()

        return self._results

    def __getitem__(self, item):
        if not self._results:
            self._results = self._results_getter()

        return self._results[item]

    def __iter__(self):
        if not self._results:
            self._results = self._results_getter()

        return iter(self._results)

    def __len__(self):
        if not self._results:
            self._results = self._results_getter()

        return len(self._results)

    def __getattr__(self, item):
        if not self._results:
            self._results = self._results_getter()

        return getattr(self._results, item)

    def __call__(self, *args, **kwargs):
        return self._relation(*args, **kwargs)
