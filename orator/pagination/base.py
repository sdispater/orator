# -*- coding: utf-8 -*-


class BasePaginator(object):

    _current_page_resolver = None

    def _is_valid_page_number(self, page):
        """
        Determine if the given value is a valid page number.

        :param page: The given page number
        :type page: int

        :rtype: bool
        """
        return isinstance(page, int) and page >= 1

    @property
    def items(self):
        """
        Get the slice of items being paginated.

        :rtype: list
        """
        return self._items.all()

    @property
    def first_item(self):
        """
        Get the number of the first item in the slice.

        :rtype: int
        """
        return (self.current_page - 1) * self.per_page + 1

    @property
    def last_item(self):
        """
        Get the number of the last item in the slice.

        :rtype: int
        """
        return self.first_item + self.count() - 1

    def has_pages(self):
        """
        Determine if there are enough items to split into multiple pages.

        :rtype: int
        """
        return not (self.current_page == 1 and not self.has_more_pages())

    def is_empty(self):
        """
        Determine if the list of items is empty or not.

        :rtype: bool
        """
        return self._items.is_empty()

    def count(self):
        """
        Get the number of items for the current page.

        :rtype: int
        """
        return len(self._items)

    @property
    def previous_page(self):
        if self.current_page > 1:
            return self.current_page - 1

    @property
    def next_page(self):
        if self.has_more_pages():
            return self.current_page + 1

    def get_collection(self):
        return self._items

    @classmethod
    def resolve_current_page(cls, default=1):
        if cls._current_page_resolver is not None:
            return cls._current_page_resolver()

        return default

    @classmethod
    def current_page_resolver(cls, resolver):
        cls._current_page_resolver = staticmethod(resolver)

    def __len__(self):
        return self.count()

    def __iter__(self):
        for item in self._items:
            yield item

    def __getitem__(self, item):
        return self.items[item]
