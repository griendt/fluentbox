from __future__ import annotations

import collections.abc as abc
import numbers
import operator
from abc import ABC
from typing import final, Any, cast


class SizedIterable(abc.Sized, abc.Iterable, ABC):
    """Intersection type for `abc.Sized` and `abc.Iterable`."""
    pass


class Box(abc.Iterable):
    _items: abc.Iterable
    _OPERATOR_MAPPING: dict[str, abc.Callable[[Any, Any], bool]] = {
        "=": operator.eq,
        "==": operator.eq,
        "!=": operator.ne,
        "<>": operator.ne,
        "<=": operator.le,
        ">=": operator.ge,
        "<": operator.lt,
        ">": operator.gt,
    }

    def __init__(self, items: abc.Iterable):
        if not hasattr(self, "_items"):
            self._items = items

    def __bool__(self) -> bool:
        return bool(self._items)

    def __contains__(self, obj: object) -> bool:
        return obj in self._items

    def __iter__(self) -> abc.Generator:
        yield from self._items

    @final
    @property
    def item_type(self) -> type:
        return type(self._items)

    def chunk(self, chunk_size: int) -> Box:
        def generator() -> abc.Generator:
            chunk = []

            for value in self:
                chunk.append(value)

                if len(chunk) == chunk_size:
                    yield chunk

        return type(self)(generator())

    def diff(self, other: abc.Iterable) -> Box:
        return self._new(value for value in self if value not in other)

    def each(self, callback: abc.Callable) -> Box:
        for value in self:
            callback(value)

        return self

    def filter(self, callback: abc.Callable | None = None) -> Box:
        if callback is None:
            callback = bool

        return self._new(value for value in self if callback(value))

    def first(self, or_fail: bool = False) -> Any:
        for value in self:
            return value

        if or_fail:
            raise IndexError

    def first_or_fail(self) -> Any:
        return self.first(or_fail=True)

    def first_where(self, key: str, operation: str | None = None, value: Any = None, /, or_fail: bool = False) -> Any:
        for item in self:
            if self._where(item, key, operation, value):
                return item

        if or_fail:
            raise IndexError

    def first_where_or_fail(self, key: str, operation: str | None = None, value: Any = None) -> Any:
        return self.first_where(key, operation, value, or_fail=True)

    def map(self, callback: abc.Callable) -> Box:
        return self._new(callback(value) for value in self)

    def merge(self, other: abc.Iterable) -> Box:
        def generator() -> abc.Generator:
            yield from self
            yield from other

        return self._new(generator())

    def pluck(self, key: str, *, default: Any = None, raise_on_error: bool = False) -> Box:
        def get_attribute_or_key(obj: object) -> Any:
            if hasattr(obj, key):
                return getattr(obj, key)

            elif isinstance(obj, abc.Mapping) and key in obj.keys():
                return obj[key]

            if raise_on_error:
                raise KeyError("Object of type {} does not have key or attribute {}".format(type(obj), key))

            return default

        return self.map(lambda item: get_attribute_or_key(item))

    def reduce(self, callback: abc.Callable, initial_value: Any = None) -> Any:
        result = initial_value
        is_first_iteration = True

        for value in self:
            if is_first_iteration and result is None:
                result = value
                is_first_iteration = False

            else:
                result = callback(result, value)

        return result

    def sum(self) -> Any:
        return self.reduce(lambda x, y: x + y)

    def _new(self, items: abc.Iterable) -> Box:
        return type(self)(self.item_type(items))

    @final
    def _where(self, obj: object, key: str, operation: str | None = None, value: Any = None) -> bool:
        if hasattr(obj, key):
            obj = getattr(obj, key)

        elif isinstance(obj, abc.Mapping):
            obj = obj[key]

        else:
            raise ValueError(f"Object {obj} has no attribute or item {key}")

        if operation is None:
            # If no operator was given, we will simply check if the attribute is truthy.
            return bool(obj)

        if operation not in self._OPERATOR_MAPPING:
            raise ValueError(f"Invalid operator: '{operation}'")

        return self._OPERATOR_MAPPING[operation](obj, value)

    def where(self, key: str, operation: str | None = None, value: Any = None) -> Box:
        return self.filter(lambda obj: self._where(obj, key, operation, value))

    def zip(self, other: abc.Iterable) -> Box:
        return self._new(zip(self, other))


class SizedBox(abc.Sized, Box):
    _items: SizedIterable

    def __len__(self) -> int:
        return len(self._items)

    def average(self) -> Any:
        if not self:
            raise ZeroDivisionError

        assert isinstance(the_sum := self.sum(), numbers.Complex)
        return the_sum / len(self)


class SequenceBox(SizedBox, abc.Sequence):
    _items: abc.Sequence

    def __init__(self, items: Any):
        super().__init__(items)

        if isinstance(items, abc.Sequence):
            self.items = items

        else:
            self.items = [items]

    def _new(self, items: abc.Iterable) -> SequenceBox:
        return cast(SequenceBox, super()._new(items))

    def __getitem__(self, index: int | slice) -> Any:
        return self.items[index]

    def chunk(self, chunk_size: int) -> SequenceBox:
        # Using slices is more efficient than using the for-loop implementation in `Box`.
        return self._new(self[i: i + chunk_size] for i in range(0, len(self), chunk_size))

    def reverse(self) -> SequenceBox:
        return self._new(reversed(self))


class MappingBox(SizedBox, abc.Mapping):
    _items: abc.Mapping

    def __getitem__(self, key: abc.Hashable) -> Any:
        return self._items[key]


class MutableMappingBox(MappingBox, abc.MutableMapping):
    _items: abc.MutableMapping

    def __setitem__(self, key: abc.Hashable, value: Any) -> None:
        self._items[key] = value

    def __delitem__(self, key: abc.Hashable) -> None:
        del self._items[key]


class MutableSetBox(SizedBox, abc.MutableSet):
    _items: abc.MutableSet

    def add(self, value: Any) -> None:
        self._items.add(value)

    def discard(self, value: Any) -> None:
        self._items.discard(value)


def box(items: abc.Iterable | None = None):
    if items is None:
        return box([])

    if not isinstance(items, abc.Iterable):
        return box([items])

    if isinstance(items, abc.MutableSet):
        return MutableSetBox(items)

    if isinstance(items, abc.MutableMapping):
        return MutableMappingBox(items)

    if isinstance(items, abc.Mapping):
        return MappingBox(items)

    if isinstance(items, abc.Sequence):
        return SequenceBox(items)

    if isinstance(items, SizedIterable):
        return SizedBox(items)

    raise TypeError("Cannot create Box instance from item type {}".format(type(items)))
