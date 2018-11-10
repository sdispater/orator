# -*- coding: utf-8 -*-

from .. import OratorTestCase
from orator.support.collection import Collection


class CollectionTestCase(OratorTestCase):
    def test_first_returns_first_item_in_collection(self):
        c = Collection(["foo", "bar"])

        self.assertEqual("foo", c.first())

    def test_last_returns_last_item_in_collection(self):
        c = Collection(["foo", "bar"])

        self.assertEqual("bar", c.last())

    def test_pop_removes_and_returns_last_item_or_specified_index(self):
        c = Collection(["foo", "bar"])

        self.assertEqual("bar", c.pop())
        self.assertEqual("foo", c.last())

        c = Collection(["foo", "bar"])

        self.assertEqual("foo", c.pop(0))
        self.assertEqual("bar", c.first())

    def test_shift_removes_and_returns_first_item(self):
        c = Collection(["foo", "bar"])

        self.assertEqual("foo", c.shift())
        self.assertEqual("bar", c.first())

    def test_empty_collection_is_empty(self):
        c = Collection()
        c2 = Collection([])

        self.assertTrue(c.is_empty())
        self.assertTrue(c2.is_empty())

    def test_collection_is_constructed(self):
        c = Collection("foo")
        self.assertEqual(["foo"], c.all())

        c = Collection(2)
        self.assertEqual([2], c.all())

        c = Collection(False)
        self.assertEqual([False], c.all())

        c = Collection(None)
        self.assertEqual([], c.all())

        c = Collection()
        self.assertEqual([], c.all())

    def test_offset_access(self):
        c = Collection(["foo", "bar"])
        self.assertEqual("bar", c[1])

        c[1] = "baz"
        self.assertEqual("baz", c[1])

        del c[0]
        self.assertEqual("baz", c[0])

    def test_forget(self):
        c = Collection(["foo", "bar", "boom"])
        c.forget(0)
        self.assertEqual("bar", c[0])
        c.forget(0, 1)
        self.assertTrue(c.is_empty())

    def test_get_avg_items_from_collection(self):
        c = Collection([{"foo": 10}, {"foo": 20}])
        self.assertEqual(15, c.avg("foo"))

        c = Collection([1, 2, 3, 4, 5])
        self.assertEqual(3, c.avg())

        c = Collection()
        self.assertIsNone(c.avg())

    def test_collapse(self):
        obj1 = object()
        obj2 = object()

        c = Collection([[obj1], [obj2]])
        self.assertEqual([obj1, obj2], c.collapse().all())

    def test_collapse_with_nested_collection(self):
        c = Collection([Collection([1, 2, 3]), Collection([4, 5, 6])])
        self.assertEqual([1, 2, 3, 4, 5, 6], c.collapse().all())

    def test_contains(self):
        c = Collection([1, 3, 5])

        self.assertTrue(c.contains(1))
        self.assertFalse(c.contains(2))
        self.assertTrue(c.contains(lambda x: x < 5))
        self.assertFalse(c.contains(lambda x: x > 5))
        self.assertIn(3, c)

        c = Collection([{"v": 1}, {"v": 3}, {"v": 5}])
        self.assertTrue(c.contains("v", 1))
        self.assertFalse(c.contains("v", 2))

        obj1 = type("lamdbaobject", (object,), {})()
        obj1.v = 1
        obj2 = type("lamdbaobject", (object,), {})()
        obj2.v = 3
        obj3 = type("lamdbaobject", (object,), {})()
        obj3.v = 5
        c = Collection([{"v": 1}, {"v": 3}, {"v": 5}])
        self.assertTrue(c.contains("v", 1))
        self.assertFalse(c.contains("v", 2))

    def test_countable(self):
        c = Collection(["foo", "bar"])
        self.assertEqual(2, c.count())
        self.assertEqual(2, len(c))

    def test_diff(self):
        c = Collection(["foo", "bar"])
        self.assertEqual(["foo"], c.diff(Collection(["bar", "baz"])).all())

    def test_each(self):
        original = ["foo", "bar", "baz"]
        c = Collection(original)

        result = []
        c.each(lambda x: result.append(x))
        self.assertEqual(result, original)
        self.assertEqual(original, c.all())

    def test_every(self):
        c = Collection([1, 2, 3, 4, 5, 6])
        self.assertEqual([1, 3, 5], c.every(2).all())
        self.assertEqual([2, 4, 6], c.every(2, 1).all())

    def test_filter(self):
        c = Collection([{"id": 1, "name": "hello"}, {"id": 2, "name": "world"}])
        self.assertEqual(
            [{"id": 2, "name": "world"}], c.filter(lambda item: item["id"] == 2).all()
        )

        c = Collection(["", "hello", "", "world"])
        self.assertEqual(["hello", "world"], c.filter().all())

    def test_where(self):
        c = Collection([{"v": 1}, {"v": 3}, {"v": 2}, {"v": 3}, {"v": 4}])
        self.assertEqual([{"v": 3}, {"v": 3}], c.where("v", 3).all())

    def test_implode(self):
        obj1 = type("lamdbaobject", (object,), {})()
        obj1.name = "john"
        obj1.email = "foo"
        c = Collection(
            [{"name": "john", "email": "foo"}, {"name": "jane", "email": "bar"}]
        )
        self.assertEqual("foobar", c.implode("email"))
        self.assertEqual("foo,bar", c.implode("email", ","))

        c = Collection(["foo", "bar"])
        self.assertEqual("foobar", c.implode(""))
        self.assertEqual("foo,bar", c.implode(","))

    def test_lists(self):
        obj1 = type("lamdbaobject", (object,), {})()
        obj1.name = "john"
        obj1.email = "foo"
        c = Collection([obj1, {"name": "jane", "email": "bar"}])
        self.assertEqual({"john": "foo", "jane": "bar"}, c.lists("email", "name"))
        self.assertEqual(["foo", "bar"], c.pluck("email").all())

    def test_map(self):
        c = Collection([1, 2, 3, 4, 5])
        self.assertEqual([3, 4, 5, 6, 7], c.map(lambda x: x + 2).all())

    def test_merge(self):
        c = Collection([1, 2, 3])
        c.merge([4, 5, 6])
        self.assertEqual([1, 2, 3, 4, 5, 6], c.all())

        c = Collection(Collection([1, 2, 3]))
        c.merge([4, 5, 6])
        self.assertEqual([1, 2, 3, 4, 5, 6], c.all())

    def test_for_page(self):
        c = Collection([1, 2, 3, 4, 5, 6])
        self.assertEqual([4, 5, 6], c.for_page(2, 3).all())
        self.assertEqual([5, 6], c.for_page(2, 4).all())

    def test_prepend(self):
        c = Collection([4, 5, 6])
        c.prepend(3)
        self.assertEqual([3, 4, 5, 6], c.all())

    def test_append(self):
        c = Collection([3, 4, 5])
        c.append(6)
        self.assertEqual([3, 4, 5, 6], c.all())

    def test_pull(self):
        c = Collection([1, 2, 3, 4])
        c.pull(2)
        self.assertEqual([1, 2, 4], c.all())

    def test_put(self):
        c = Collection([1, 2, 4])
        c.put(2, 3)
        self.assertEqual([1, 2, 3], c.all())

    def test_reject(self):
        c = Collection([1, 2, 3, 4, 5, 6])
        self.assertEqual([1, 2, 3], c.reject(lambda x: x > 3).all())

    def test_reverse(self):
        c = Collection([1, 2, 3, 4])
        self.assertEqual([4, 3, 2, 1], c.reverse().all())

    def test_sort(self):
        c = Collection([5, 3, 1, 2, 4])

        sorted = c.sort(lambda x: x)
        self.assertEqual([1, 2, 3, 4, 5], sorted.all())

    def test_take(self):
        c = Collection([1, 2, 3, 4, 5, 6])
        self.assertEqual([1, 2, 3], c.take(3).all())
        self.assertEqual([4, 5, 6], c.take(-3).all())

    def test_transform(self):
        c = Collection([1, 2, 3, 4])
        c.transform(lambda x: x + 2)
        self.assertEqual([3, 4, 5, 6], c.all())

    def test_zip(self):
        c = Collection([1, 2, 3])
        self.assertEqual([(1, 4), (2, 5), (3, 6)], c.zip([4, 5, 6]).all())

    def test_only(self):
        c = Collection([1, 2, 3, 4, 5])
        self.assertEqual([2, 4], c.only(1, 3).all())

    def test_without(self):
        c = Collection([1, 2, 3, 4, 5])
        self.assertEqual([1, 3, 5], c.without(1, 3).all())
        self.assertEqual([1, 2, 3, 4, 5], c.all())

    def test_flatten(self):
        c = Collection({"foo": [5, 6], "bar": 7, "baz": {"boom": [1, 2, 3, 4]}})

        self.assertEqual([1, 2, 3, 4, 5, 6, 7], c.flatten().sort().all())

        c = Collection([1, [2, 3], 4])
        self.assertEqual([1, 2, 3, 4], c.flatten().all())
