import math
import unittest
from collections import abc

from vessel import Vessel


class VesselTest(unittest.TestCase):

    def test_all(self):
        for structure in ([1, 2, 3], {1, 2, 3}, {"x": 1, "y": 2, "z": 3}, (1, 2, 3)):
            self.assertEqual(Vessel(structure).all(), structure)

    def test_average(self):
        for structure in ([1, 2, 3, 5], {1, 2, 3, 5}, {"x": 1, "y": 2, "z": 3, "w": 5}, (1, 2, 3, 5)):
            self.assertEqual(2.75, Vessel(structure).average())

        with self.assertRaises(ZeroDivisionError):
            Vessel([]).average()

        # .average works with fractions.
        self.assertEqual(2, Vessel([1.5, 2.5]).average())

        # .average works with reals.
        self.assertEqual((math.pi + math.e)/2., Vessel([math.pi, math.e]).average())

        # .average works on complex numbers.
        self.assertEqual(complex(3, 4), Vessel([complex(2, 3), complex(3, 4), complex(4, 5)]).average())

    def test_contains(self):
        vessel = Vessel([1, 2, 3])
        self.assertTrue(2 in vessel)

        vessel = Vessel({1, 2, 3})
        self.assertTrue(2 in vessel)

        # In the case of Mapping classes as underlying structure, __contains__ should check for keys rather than values.
        vessel = Vessel({"x": 1, "y": 2, "z": 3})
        self.assertTrue("y" in vessel)

    def test_chunk(self):
        for structure in ([1, 2, 3, 4, 5], {"a": 1, "b": 2, "c": 3, "d": 4, "e": 5}, {1, 2, 3, 4, 5}, (1, 2, 3, 4, 5)):
            chunks = Vessel(structure).chunk(2).all()

            # .chunk creates a new Vessel of type Sequence as chunks are always ordered.
            self.assertIsInstance(chunks, abc.Sequence)

            # .chunk uses up all elements, even if it causes the last chunk to not be "full".
            self.assertEqual(3, len(chunks))
            self.assertEqual([2, 2, 1], [len(chunk) for chunk in chunks])

            # .chunk preserves the container type for each of the chunks.
            for chunk in chunks:
                self.assertIsInstance(chunk, type(structure))

            # .chunk preserves the order when the container type is a Sequence.
            if isinstance(structure, abc.Sequence):
                self.assertEqual([[1, 2], [3, 4], [5]], [list(chunk) for chunk in chunks])

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

    def test_reduce(self):
        # Reduce to the last element; no initial value is necessary.
        self.assertEqual(3, Vessel([1, 2, 3]).reduce(lambda x, y: y))

        # .reduce takes the first element as initial value if no initial value is provided.
        self.assertEqual(6, Vessel([1, 2, 3]).reduce(lambda x, y: x + y))

        # .reduce uses the initial value if provided.
        self.assertEqual(10, Vessel([1, 2, 3]).reduce(lambda x, y: x + y, 4))

        # .reduce may also effectively be a nop.
        self.assertEqual(None, Vessel([1, 2, 3]).reduce(lambda x, y: None))

    def test_sum(self):
        for structure in ([1, 2, 3, 5], {1, 2, 3, 5}, {"x": 1, "y": 2, "z": 3, "w": 5}, (1, 2, 3, 5)):
            self.assertEqual(11, Vessel(structure).sum())

        # .sum on an empty Vessel is allowed, but since the type of elements may vary,
        # returning 0 is not desired. For example, for lists the neutral element is the empty list.
        # Therefore, this call should return None.
        self.assertEqual(None, Vessel([]).sum())

        # .sum works with fractions.
        self.assertEqual(4, Vessel([1.5, 2.5]).sum())

        # .sum works with reals.
        self.assertEqual(math.pi + math.e + 3, Vessel([math.pi, math.e, 3]).sum())

        # .sum works on complex numbers.
        self.assertEqual(complex(9, 12), Vessel([complex(2, 3), complex(3, 4), complex(4, 5)]).sum())

        # .sum works on lists.
        self.assertEqual([1, 2, 3, 4, 5, 6], Vessel([[1, 2], [3, 4], [5, 6]]).sum())

        # .sum works on strings.
        self.assertEqual("abc", Vessel(["a", "b", "c"]).sum())
