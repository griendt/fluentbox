import math
import unittest
from collections import abc
from typing import Any, cast

from src.fluentbox import MappingBox, SequenceBox, MutableMappingBox, MutableSetBox, Box


class BoxTest(unittest.TestCase):
    def test_key_by_string(self) -> None:
        box = Box([{"id": 1, "name": "foo"}, {"id": 2, "name": "bar"}, {"id": 3, "name": "baz"}])

        # .key_by can look inside dictionary keys.
        # Note that the underlying data type has changed from `list` to `dict`.
        self.assertEqual({
            1: {"id": 1, "name": "foo"},
            2: {"id": 2, "name": "bar"},
            3: {"id": 3, "name": "baz"}
        }, box.key_by("id"))

        class Foo:
            name: str

            def __init__(self, name: str):
                self.name = name

        foo, bar, baz = Foo("foo"), Foo("bar"), Foo("baz")
        box = Box([foo, bar, baz])

        # .key_by can look up object attributes as well.
        self.assertEqual({
            "foo": foo,
            "bar": bar,
            "baz": baz,
        }, box.key_by("name"))


class SequenceBoxTest(unittest.TestCase):
    def test_all(self) -> None:
        for structure in ([1, 2, 3], (1, 2, 3)):
            self.assertEqual(SequenceBox(structure).all(), structure)

    def test_average(self) -> None:
        for structure in ([1, 2, 3, 5], (1, 2, 3, 5)):
            self.assertEqual(2.75, SequenceBox(structure).average())

        with self.assertRaises(ZeroDivisionError):
            SequenceBox([]).average()

        # .average works with fractions.
        self.assertEqual(2, SequenceBox([1.5, 2.5]).average())

        # .average works with reals.
        self.assertEqual((math.pi + math.e) / 2., SequenceBox([math.pi, math.e]).average())

        # .average works on complex numbers.
        self.assertEqual(complex(3, 4), SequenceBox([complex(2, 3), complex(3, 4), complex(4, 5)]).average())

    def test_contains(self) -> None:
        for structure in ([1, 2, 3], (1, 2, 3)):
            self.assertTrue(2 in SequenceBox(structure))

    def test_chunk(self) -> None:
        for structure in ([1, 2, 3, 4, 5], (1, 2, 3, 4, 5)):
            chunks = SequenceBox(structure).chunk(2).all()

            # .chunk creates a new Box of type Sequence as chunks are always ordered.
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

    def test_diff(self) -> None:
        for (first, second, expected) in [
            ([1, 2, 3], [2, 3], [1]),
            ((1, 2, 3), (2, 3), (1,)),
        ]:
            # .diff accepts both Box and non-Box arguments and gives identical results.
            self.assertEqual(expected, SequenceBox(first).diff(second).all())
            self.assertEqual(expected, SequenceBox(first).diff(SequenceBox(second)).all())

    def test_each(self) -> None:
        for structure in ([2, 3, 1], (2, 3, 1)):
            result = []
            box = SequenceBox(structure).each(lambda item: result.append(item))

            # The contents of the Box are preserved.
            self.assertEqual(box.all(), structure)

            # The callbacks are executed, in order. It also accepts immutable types as
            # underlying container, since no new container of that type needs to be built.
            self.assertEqual(result, [2, 3, 1])

    def test_filter(self) -> None:
        # .filter works on both mutable and immutable Sequence types.
        for structure in ([2, 3, 1], (2, 3, 1)):
            box = cast(SequenceBox, SequenceBox(structure).filter(lambda item: item > 2))

            self.assertEqual(1, len(box))
            self.assertEqual(3, box[0])

        # .filter without arguments does a truthy check.
        self.assertEqual([6], SequenceBox([0, False, None, 6]).filter().all())

    def test_first(self) -> None:
        for structure in ([2, 3, 1], (2, 3, 1)):
            box = SequenceBox(structure)

            self.assertEqual(2, box.first())
            # Of course, instead of .first the user may also make use of __getitem__.
            self.assertEqual(2, box[0])

    def test_first_or_fail(self) -> None:
        empty_structure: abc.Sequence
        for empty_structure in ([], ()):
            with self.assertRaises(IndexError):
                SequenceBox(empty_structure).first_or_fail()

    def test_initialize(self) -> None:
        self.assertIsInstance(SequenceBox([1, 2, 3]), SequenceBox)
        self.assertIsInstance(SequenceBox({1, 2, 3}), SequenceBox)
        self.assertIsInstance(SequenceBox({"x": 1, "y": 2, "z": 3}), SequenceBox)

        # Despite being immutable, instantiating from a tuple is allowed.
        self.assertIsInstance(SequenceBox((1, 2, 3)), SequenceBox)

        # Instantiating from a non-Collection is allowed; it will be wrapped in a list.
        # In particular, strings are not considered as a valid container class.
        box = SequenceBox("foo")
        self.assertIsInstance(box, SequenceBox)
        self.assertTrue(1, len(box))
        self.assertTrue(type(SequenceBox("foo").all()), list)

    def test_map(self) -> None:
        self.assertEqual(SequenceBox([2, 3, 1]).map(lambda item: item + 3).all(), [5, 6, 4])

        # .map also works when the underlying type is immutable.
        self.assertEqual(SequenceBox((1, 2, 3)).map(lambda item: item * 2).all(), (2, 4, 6))

    def test_merge(self) -> None:

        # .merge works on Boxed or non-Boxed lists and tuples as expected.
        self.assertEqual([1, 2, 3, 4], SequenceBox([1, 2]).merge([3, 4]).all())
        self.assertEqual([1, 2, 3, 4], SequenceBox([1, 2]).merge(SequenceBox([3, 4])).all())

        self.assertEqual((1, 2, 3, 4), SequenceBox((1, 2)).merge((3, 4)).all())
        self.assertEqual((1, 2, 3, 4), SequenceBox((1, 2)).merge(SequenceBox((3, 4))).all())

    def test_pluck(self) -> None:
        # .pluck can fetch keys from mapping objects.
        self.assertEqual([1, 2, 3, 4], SequenceBox([{"x": 1}, {"x": 2}, {"x": 3}, {"x": 4}]).pluck("x").all())

        # .pluck returns the default argument (default: None) if a key does not exist.
        self.assertEqual([None], SequenceBox([{"x": 1, "y": 2}]).pluck("z").all())

        # .pluck accepts a default argument and will return that if the key does not exist.
        self.assertEqual([2], SequenceBox([{"x": 1, "y": 2}]).pluck("y", default=3).all())
        self.assertEqual([3], SequenceBox([{"x": 1, "y": 2}]).pluck("z", default=3).all())

        # .pluck will raise a KeyError if specified to do so, when trying to pluck a non-existing key.
        with self.assertRaises(KeyError):
            SequenceBox([{"x": 1, "y": 2}]).pluck("z", raise_on_error=True)

        # .pluck also works on objects that have the given key as an attribute.
        class Foo:
            def __init__(self, x: int = 3, y: int = 4):
                self.x = x
                self.y = y

        self.assertEqual([1, 2], SequenceBox([Foo(x=1, y=3), Foo(x=2, y=2)]).pluck("x").all())

    def test_reduce(self) -> None:
        # Reduce to the last element; no initial value is necessary.
        self.assertEqual(3, SequenceBox([1, 2, 3]).reduce(lambda x, y: y))

        # .reduce takes the first element as initial value if no initial value is provided.
        self.assertEqual(6, SequenceBox([1, 2, 3]).reduce(lambda x, y: x + y))

        # .reduce uses the initial value if provided.
        self.assertEqual(10, SequenceBox([1, 2, 3]).reduce(lambda x, y: x + y, 4))

        # .reduce may also effectively be a nop.
        self.assertEqual(None, SequenceBox([1, 2, 3]).reduce(lambda x, y: None))

    def test_reverse(self) -> None:
        self.assertEqual([3, 2, 1], SequenceBox([1, 2, 3]).reverse().all())
        self.assertEqual((3, 2, 1), SequenceBox((1, 2, 3)).reverse().all())

    def test_sum(self) -> None:
        for structure in ([1, 2, 3, 5], (1, 2, 3, 5)):
            self.assertEqual(11, SequenceBox(structure).sum())

        # .sum on an empty Box is allowed, but since the type of elements may vary,
        # returning 0 is not desired. For example, for lists the neutral element is the empty list.
        # Therefore, this call should return None.
        self.assertEqual(None, SequenceBox([]).sum())

        # .sum works with fractions.
        self.assertEqual(4, SequenceBox([1.5, 2.5]).sum())

        # .sum works with reals.
        self.assertEqual(math.pi + math.e + 3, SequenceBox([math.pi, math.e, 3]).sum())

        # .sum works on complex numbers.
        self.assertEqual(complex(9, 12), SequenceBox([complex(2, 3), complex(3, 4), complex(4, 5)]).sum())

        # .sum works on lists.
        self.assertEqual([1, 2, 3, 4, 5, 6], SequenceBox([[1, 2], [3, 4], [5, 6]]).sum())

        # .sum works on strings.
        self.assertEqual("abc", SequenceBox(["a", "b", "c"]).sum())

    def test_first_where(self) -> None:
        box = SequenceBox([{"name": "X", "id": 1}, {"name": "Y", "id": 2}, {"name": "X", "id": 3}])

        # .first_where should return the first matching item.
        self.assertEqual(1, box.first_where("name", "==", "X")["id"])

        # .first_where returns None if no item matches, by default.
        self.assertEqual(None, box.first_where("name", "==", "Z"))

        # .first_where raises an error if or_fail is set to True.
        with self.assertRaises(IndexError):
            box.first_where("name", "==", "Z", or_fail=True)

    def test_first_where_or_fail(self) -> None:
        box = SequenceBox([{"name": "X", "id": 1}, {"name": "Y", "id": 2}, {"name": "X", "id": 3}])

        # .first_where_or_fail should return the first matching item.
        self.assertEqual(1, box.first_where_or_fail("name", "==", "X")["id"])

        # .first_where_or_fail should throw an error if no matching item is found.
        with self.assertRaises(IndexError):
            box.first_where_or_fail("name", "==", "Z")

    def test_where(self) -> None:
        box = SequenceBox([{"name": "X", "id": 1}, {"name": "Y", "id": 2}, {"name": "X", "id": 3}])

        # Normal operators work on dictionaries.
        self.assertEqual(box.where("name", "==", "X").all(), [{"name": "X", "id": 1}, {"name": "X", "id": 3}])
        self.assertEqual(box.where("name", "!=", "X").all(), [{"name": "Y", "id": 2}])
        self.assertEqual(box.where("id", "<=", 2).all(), [{"name": "X", "id": 1}, {"name": "Y", "id": 2}])
        self.assertEqual(box.where("id", "<", 2).all(), [{"name": "X", "id": 1}])
        self.assertEqual(box.where("id", ">=", 2).all(), [{"name": "Y", "id": 2}, {"name": "X", "id": 3}])
        self.assertEqual(box.where("id", ">", 2).all(), [{"name": "X", "id": 3}])

        box = SequenceBox([{"value": True}, {"value": False}, {"value": None}, {"value": 0}, {"value": []}])

        # No operation defined should default to a truthy-check.
        self.assertEqual(box.where("value").all(), [{"value": True}])

        class Dummy:
            def __init__(self, dummy_id: int, name: str, value: Any = None):
                self.id = dummy_id
                self.name = name
                self.value = value

        obj_1, obj_2, obj_3 = Dummy(1, "X", []), Dummy(2, "Y", {}), Dummy(3, "X", 100)
        box = SequenceBox([obj_1, obj_2, obj_3])

        # Common operators work on objects as well, using their attributes.
        self.assertEqual(box.where("name", "==", "X").all(), [obj_1, obj_3])
        self.assertEqual(box.where("name", "!=", "X").all(), [obj_2])
        self.assertEqual(box.where("id", "<=", 2).all(), [obj_1, obj_2])
        self.assertEqual(box.where("id", ">=", 2).all(), [obj_2, obj_3])
        self.assertEqual(box.where("id", "<", 2).all(), [obj_1])
        self.assertEqual(box.where("id", ">", 2).all(), [obj_3])

        # No operation defined should default to a truthy-check on objects' attributes as well.
        self.assertEqual(box.where("value").all(), [obj_3])

    def test_zip(self) -> None:
        # .zip works on lists and tuples as expected.
        self.assertEqual([(1, 3), (2, 4)], SequenceBox([1, 2]).zip([3, 4]).all())
        self.assertEqual(((1, 3), (2, 4)), SequenceBox((1, 2)).zip((3, 4)).all())

        # .zip also accepts a Box as input, if their content type is appropriate.
        self.assertEqual([(1, 3), (2, 4)], SequenceBox([1, 2]).zip(SequenceBox([3, 4])).all())
        self.assertEqual(((1, 3), (2, 4)), SequenceBox((1, 2)).zip(SequenceBox((3, 4))).all())


class MappingBoxTest(unittest.TestCase):

    def test_getitem(self) -> None:
        self.assertEqual("bar", MappingBox({"foo": "bar"})["foo"])

        with self.assertRaises(KeyError):
            _ = MappingBox({"foo": "bar"})["baz"]


class MutableMappingBoxTest(unittest.TestCase):

    def test_setitem(self) -> None:
        box = MutableMappingBox({"foo": "bar"})
        box["baz"] = 3

        self.assertEqual(box["foo"], "bar")
        self.assertEqual(box["baz"], 3)

    def test_delitem(self) -> None:
        box = MutableMappingBox({"foo": "bar"})
        del box["foo"]

        self.assertEqual(0, len(box))


class MutableSetBoxTest(unittest.TestCase):

    def test_add(self) -> None:
        box = MutableSetBox({1, 2, 3})
        box.add(4)

        self.assertEqual(4, len(box))
        self.assertTrue(4 in box)

        box.add(2)

        self.assertEqual(4, len(box))

    def test_discard(self) -> None:
        box = MutableSetBox({1, 2, 3})
        box.discard(2)

        self.assertEqual(2, len(box))
        self.assertTrue(1 in box)
        self.assertTrue(3 in box)
