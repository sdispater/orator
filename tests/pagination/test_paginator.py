# -*- coding: utf-8 -*-

from orator.pagination import Paginator
from .. import OratorTestCase


class PaginatorTestCase(OratorTestCase):
    def test_returns_relevant_context(self):
        p = Paginator(["item3", "item4", "item5"], 2, 2)

        self.assertEqual(2, p.current_page)
        self.assertTrue(p.has_pages())
        self.assertTrue(p.has_more_pages())
        self.assertEqual(["item3", "item4"], p.items)
        self.assertEqual(2, p.per_page)
        self.assertEqual(3, p.next_page)
        self.assertEqual(1, p.previous_page)
        self.assertEqual(3, p.first_item)
        self.assertEqual(4, p.last_item)

        self.assertEqual("item4", p[1])

    def test_current_page_resolver(self):
        def current_page_resolver():
            return 7

        Paginator.current_page_resolver(current_page_resolver)
        self.assertEqual(7, Paginator.resolve_current_page())
