import unittest
from collections import abc

from src import Vessel


class VesselTest(unittest.TestCase):

    def test_all(self):
        for structure in ([1, 2, 3], {1, 2, 3}, {"x": 1, "y": 2, "z": 3}):
            self.assertEqual(Vessel(structure).all(), structure)

    def test_contains(self):
        vessel = Vessel([1, 2, 3])
        self.assertTrue(2 in vessel)

        vessel = Vessel({1, 2, 3})
        self.assertTrue(2 in vessel)

        # In the case of Mapping classes as underlying structure, __contains__ should check for keys rather than values.
        vessel = Vessel({"x": 1, "y": 2, "z": 3})
        self.assertTrue("y" in vessel)

    def test_each(self):
        for structure in ([2, 3, 1], {1, 2, 3}, {"x": 1, "y": 2, "z": 3}, (2, 3, 1)):
            result = []
            vessel = Vessel(structure).each(lambda item: result.append(item))

            # The contents of the Vessel are preserved
            self.assertEqual(vessel.all(), structure)

            # The callbacks are executed, in order where applicable. It also accepts immutable types as
            # underlying container, since no new container of that type needs to be built.
            if isinstance(structure, abc.Sequence):
                self.assertEqual(result, [2, 3, 1])

            else:
                self.assertEqual(set(result), {1, 2, 3})

    def test_filter(self):
        for structure in ([2, 3, 1], {1, 2, 3}, {"x": 1, "y": 2, "z": 3}):
            vessel = Vessel(structure).filter(lambda item: item > 2)

            self.assertEqual(1, len(vessel))

            for _, value in vessel.items():
                self.assertEqual(3, value)

        # .filter will also work on immutable types.
        self.assertEqual((1, 2, 3), Vessel((1, 2, 0, 3)).filter(lambda item: item > 0).all())

        # .filter without arguments does a truthy check.
        self.assertEqual([6], Vessel([0, False, None, 6]).filter().all())

    def test_first(self):
        for structure in ([2, 3, 1], {1, 2, 3}, {"x": 1, "y": 2, "z": 3}, (2, 3, 1)):
            vessel = Vessel(structure)

            # When the underlying structure is Sequence
            if isinstance(structure, abc.Sequence):
                self.assertEqual(vessel.first(), 2)

            else:
                self.assertTrue(vessel.first() in {1, 2, 3})

    def test_first_or_fail(self):
        for empty_structure in ([], {}, set(), tuple()):
            with self.assertRaises(IndexError):
                Vessel(empty_structure).first_or_fail()

    def test_initialize(self):
        self.assertIsInstance(Vessel([1, 2, 3]), Vessel)
        self.assertIsInstance(Vessel({1, 2, 3}), Vessel)
        self.assertIsInstance(Vessel({"x": 1, "y": 2, "z": 3}), Vessel)

        # Despite being immutable, instantiating from a tuple is allowed.
        self.assertIsInstance(Vessel((1, 2, 3)), Vessel)

        # Instantiating from a non-Collection is allowed; it will be wrapped in a list.
        # In particular, strings are not considered as a valid container class.
        vessel = Vessel("foo")
        self.assertIsInstance(vessel, Vessel)
        self.assertTrue(1, len(vessel))
        self.assertTrue(type(Vessel("foo")._items), list)

    def test_map(self):
        self.assertEqual(Vessel([2, 3, 1]).map(lambda item: item + 3).all(), [5, 6, 4])
        self.assertEqual(Vessel({2, 3, 1}).map(lambda item: item + 3).all(), {5, 6, 4})

        # .map should apply the callback to the values and preserve the keys.
        self.assertEqual(Vessel({"x": 2, "y": 3, "z": 1}).map(lambda item: item + 3).all(), {"x": 5, "y": 6, "z": 4})

        # .map also attempts to work when the underlying type is immutable.
        self.assertEqual(Vessel((1, 2, 3)).map(lambda item: item * 2).all(), (2, 4, 6))
