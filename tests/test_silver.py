import unittest
from collections import abc

from silver import Silver


class SilverTest(unittest.TestCase):

    def test_all(self):
        for structure in ([1, 2, 3], {1, 2, 3}, {"x": 1, "y": 2, "z": 3}):
            self.assertEqual(Silver(structure).all(), structure)

    def test_contains(self):
        silver = Silver([1, 2, 3])
        self.assertTrue(2 in silver)

        silver = Silver({1, 2, 3})
        self.assertTrue(2 in silver)

        # In the case of Mapping classes as underlying structure, __contains__ should check for keys rather than values.
        silver = Silver({"x": 1, "y": 2, "z": 3})
        self.assertTrue("y" in silver)

    def test_each(self):
        for structure in ([2, 3, 1], {1, 2, 3}, {"x": 1, "y": 2, "z": 3}, (2, 3, 1)):
            result = []
            silver = Silver(structure).each(lambda item: result.append(item))

            # The contents of the Silver are preserved
            self.assertEqual(silver.all(), structure)

            # The callbacks are executed, in order where applicable. It also accepts immutable types as
            # underlying container, since no new container of that type needs to be built.
            if isinstance(structure, abc.Sequence):
                self.assertEqual(result, [2, 3, 1])

            else:
                self.assertEqual(set(result), {1, 2, 3})

    def test_filter(self):
        for structure in ([2, 3, 1], {1, 2, 3}, {"x": 1, "y": 2, "z": 3}):
            silver = Silver(structure).filter(lambda item: item > 2)

            self.assertEqual(1, len(silver))

            for _, value in silver.items():
                self.assertEqual(3, value)

        # Since .filter needs to build a new underlying container instance, only Mutable types as underlying
        # containers are accepted.
        with self.assertRaises(TypeError):
            Silver((1, 2, 3)).filter(lambda item: item)

        # .filter without arguments does a truthy check.
        self.assertEqual([6], Silver([0, False, None, 6]).filter().all())

    def test_first(self):
        for structure in ([2, 3, 1], {1, 2, 3}, {"x": 1, "y": 2, "z": 3}, (2, 3, 1)):
            silver = Silver(structure)

            # When the underlying structure is Sequence
            if isinstance(structure, abc.Sequence):
                self.assertEqual(silver.first(), 2)

            else:
                self.assertTrue(silver.first() in {1, 2, 3})

    def test_first_or_fail(self):
        for empty_structure in ([], {}, set(), tuple()):
            with self.assertRaises(IndexError):
                Silver(empty_structure).first_or_fail()

    def test_initialize(self):
        self.assertIsInstance(Silver([1, 2, 3]), Silver)
        self.assertIsInstance(Silver({1, 2, 3}), Silver)
        self.assertIsInstance(Silver({"x": 1, "y": 2, "z": 3}), Silver)

        # Despite being immutable, instantiating from a tuple is allowed.
        self.assertIsInstance(Silver((1, 2, 3)), Silver)

        # Instantiating from a non-Collection is allowed; it will be wrapped in a list.
        # In particular, strings are not considered as a valid container class.
        silver = Silver("foo")
        self.assertIsInstance(silver, Silver)
        self.assertTrue(1, len(silver))
        self.assertTrue(type(Silver("foo")._items), list)

    def test_map(self):
        self.assertEqual(Silver([2, 3, 1]).map(lambda item: item + 3).all(), [5, 6, 4])
        self.assertEqual(Silver({2, 3, 1}).map(lambda item: item + 3).all(), {5, 6, 4})

        # .map should apply the callback to the values and preserve the keys.
        self.assertEqual(Silver({"x": 2, "y": 3, "z": 1}).map(lambda item: item + 3).all(), {"x": 5, "y": 6, "z": 4})

        # .map requires the underlying container type to be Mutable in order to build a return value.
        with self.assertRaises(TypeError):
            Silver((1, 2, 3)).map(lambda item: item)
