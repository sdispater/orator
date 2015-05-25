# -*- coding: utf-8 -*-

from orator.pagination import LengthAwarePaginator
from .. import OratorTestCase


class LengthAwarePaginatorTestCase(OratorTestCase):

    def test_returns_relevant_context(self):
        p = LengthAwarePaginator(['item3', 'item4'], 4, 2, 2)

        self.assertEqual(2, p.current_page)
        self.assertEqual(2, p.last_page)
        self.assertEqual(4, p.total)
        self.assertTrue(p.has_pages())
        self.assertFalse(p.has_more_pages())
        self.assertEqual(['item3', 'item4'], p.items)
        self.assertEqual(2, p.per_page)
        self.assertIsNone(p.next_page)
        self.assertEqual(1, p.previous_page)
        self.assertEqual(3, p.first_item)
        self.assertEqual(4, p.last_item)

        self.assertEqual('item4', p[1])
