# -*- coding: utf-8 -*-

from .base import BasePaginator
from ..support.collection import Collection
from ..utils import deprecated


class Paginator(BasePaginator):
    def __init__(self, items, per_page, current_page=None, options=None):
        """
        Constructor

        :param items: The items being paginated
        :type items: mixed

        :param per_page: The number of results per page
        :type per_page: int

        :param current_page: The current page of results
        :type current_page: int

        :param options: Extra options to set
        :type options: dict
        """
        if options is not None:
            for key, value in options.items():
                setattr(self, key, value)

        self.per_page = per_page
        self.current_page = self._set_current_page(current_page)
        if isinstance(items, Collection):
            self._items = items
        else:
            self._items = Collection.make(items)

        self._check_for_more_pages()

    def _set_current_page(self, current_page):
        """
        Get the current page for the request.

        :param current_page: The current page of results
        :type current_page: int

        :rtype: int
        """
        if not current_page:
            self.resolve_current_page()

        if not self._is_valid_page_number(current_page):
            return 1

        return current_page

    def _check_for_more_pages(self):
        """
        Check for more pages. The last item will be sliced off.
        """
        self._has_more = len(self._items) > self.per_page

        self._items = self._items[0 : self.per_page]

    def has_more_pages(self):
        """
        Determine if there are more items in the data source.

        :rtype: int
        """
        return self._has_more

    @deprecated
    def to_dict(self):
        """
        Alias for serialize.

        :rtype: list
        """
        return self.serialize()

    def serialize(self):
        """
        Convert the object into something JSON serializable.

        :rtype: list
        """
        return self._items.serialize()

    def to_json(self, **options):
        return self._items.to_json(**options)
