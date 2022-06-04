from __future__ import annotations

import collections.abc as abc
import numbers
import operator
from typing import final, Any, Literal


class Box:
    _items: abc.Collection
    _operator_mapping: dict[str, abc.Callable] = {
        "=": operator.eq,
        "==": operator.eq,
        "!=": operator.ne,
        "<>": operator.ne,
        "<=": operator.le,
        ">=": operator.ge,
        "<": operator.lt,
        ">": operator.gt,
    }

    def __init__(self, items):
        if isinstance(items, abc.Collection):
            self._items = items

        else:
            self._items = [items]

    def __contains__(self, obj: object):
        return obj in self._items

    def __len__(self) -> int:
        return len(self._items)

    def __iter__(self):
        for value in self._items:
            yield value

    @final
    def _new(self, items: abc.Collection):
        return type(self)(self.item_type(items))

    @final
    @property
    def item_type(self) -> type:
        return type(self._items)

    def all(self) -> abc.Collection:
        return self._items

    def chunk(self, group_size: int) -> Box:
        chunks = []
        chunk = {}

        for key, value in self.items():
            chunk[key] = value

            if len(chunk) == group_size:
                chunks.append(chunk)
                chunk = {}

        if len(chunk) > 0:
            chunks.append(chunk)

        if not issubclass(self.item_type, abc.Mapping):
            chunks = [self.item_type(chunk.values()) for chunk in chunks]  # type: ignore

        # We do not use _new because the item type for the new Vessel is by construction list,
        # which may differ from this instance's item type.
        return type(self)(chunks)

    def each(self, callback: abc.Callable) -> Box:
        for _, value in self.items():
            callback(value)

        return self

    def filter(self, callback: abc.Callable = None) -> Box:
        new_items = type(self._items)()

        if callback is None:
            callback = bool

        if isinstance(new_items, abc.Mapping):
            new_keys = {key for key, value in self.items() if callback(value)}
            return self._new({key: value for key, value in self.items() if key in new_keys})

        return self._new([value for _, value in self.items() if callback(value)])

    def first(self, or_fail: bool = False):
        for _, value in self.items():
            return value

        if or_fail:
            raise IndexError

    def first_or_fail(self):
        return self.first(or_fail=True)

    def items(self):
        if isinstance(self._items, abc.Mapping):
            for key, value in self._items.items():
                yield key, value

        else:
            for key, value in enumerate(self._items):
                yield key, value

    def map(self, callback: abc.Callable) -> Box:
        if isinstance(self._items, abc.Mapping):
            return self._new({key: callback(value) for key, value in self.items()})

        return self._new([callback(value) for _, value in self.items()])

    def average(self) -> numbers.Complex:
        if not self:
            raise ZeroDivisionError

        assert isinstance(the_sum := self.sum(), numbers.Complex)
        return the_sum / len(self)

    def sum(self) -> numbers.Complex | Literal[0]:
        return self.reduce(lambda x, y: x + y)

    def reduce(self, fn: abc.Callable, initial_value: Any = None) -> Any:
        result = initial_value
        is_first_iteration = True

        for _, value in self.items():
            if is_first_iteration and result is None:
                result = value
                is_first_iteration = False

            else:
                result = fn(result, value)

        return result

    def where(self, key: str, operation: str | None = None, value: Any = None):
        def callback(obj: object) -> bool:
            if hasattr(obj, key):
                obj = getattr(obj, key)

            elif isinstance(obj, abc.Mapping):
                obj = obj[key]

            else:
                raise ValueError(f"Object {obj} has no attribute or item {key}")

            if operation is None:
                # If no operator was given, we will simply check if the attribute is truthy.
                return bool(obj)

            if operation not in self._operator_mapping:
                raise ValueError(f"Invalid operator: '{operation}'")

            return self._operator_mapping[operation](obj, value)

        return self.filter(lambda obj: callback(obj))


__all__ = ["Box"]
