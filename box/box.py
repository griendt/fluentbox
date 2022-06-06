from __future__ import annotations

import collections.abc as abc
import itertools
import numbers
import operator
from abc import ABC, abstractmethod
from typing import final, Any, Literal


class BoxAbstract(ABC):
    items: abc.Iterable
    _OPERATOR_MAPPING: dict[str, abc.Callable] = {
        "=": operator.eq,
        "==": operator.eq,
        "!=": operator.ne,
        "<>": operator.ne,
        "<=": operator.le,
        ">=": operator.ge,
        "<": operator.lt,
        ">": operator.gt,
    }

    def __init__(self, items, *args, **kwargs):
        if not hasattr(self, "items"):
            self.items = items

    def __iter__(self):
        yield from self.items

    @abstractmethod
    def _new(self, items) -> BoxAbstract:
        pass

    @final
    def _where(self, obj: object, key: str, operation: str | None = None, value: Any = None):
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

    @final
    @property
    def item_type(self) -> type:
        return type(self.items)

    def chunk(self, chunk_size: int) -> BoxAbstract:
        def generator():
            chunk = []

            for value in self:
                chunk.append(value)

                if len(chunk) == chunk_size:
                    yield chunk

        return type(self)(generator)

    def each(self, callback: abc.Callable) -> BoxAbstract:
        for value in self:
            callback(value)

        return self

    def filter(self, callback: abc.Callable = None) -> BoxAbstract:
        def generator(fn: abc.Callable):
            if fn is None:
                fn = bool

            for value in self:
                if fn(value):
                    yield value

        return type(self)(generator(callback))


class SequenceBox(BoxAbstract, abc.Sequence):
    items: abc.Sequence

    def __init__(self, items):
        super().__init__(items)

        if isinstance(items, abc.Sequence):
            self.items = items

        else:
            self.items = [items]

    def __contains__(self, obj: object):
        return obj in self.items

    def __len__(self) -> int:
        return len(self.items)

    def __getitem__(self, index):
        return self.items[index]

    @final
    def _new(self, items: abc.Sequence | abc.Set | itertools.chain | abc.Generator | zip) -> SequenceBox:
        return type(self)(self.item_type(items))

    def chunk(self, chunk_size: int) -> SequenceBox:
        return self._new(self[i: i + chunk_size] for i in range(0, len(self), chunk_size))

    def diff(self, other: abc.Sequence | abc.Set):
        return self._new(value for value in self if value not in other)

    def each(self, callback: abc.Callable) -> SequenceBox:
        for value in self:
            callback(value)

        return self

    def filter(self, callback: abc.Callable = None) -> SequenceBox:
        if callback is None:
            callback = bool

        return self._new(value for value in self if callback(value))

    def first(self, or_fail: bool = False):
        for value in self:
            return value

        if or_fail:
            raise IndexError

    def first_or_fail(self):
        return self.first(or_fail=True)

    def first_where(self, key: str, operation: str | None = None, value: Any = None, /, or_fail: bool = False):
        for item in self:
            if self._where(item, key, operation, value):
                return item

        if or_fail:
            raise IndexError

    def first_where_or_fail(self, key: str, operation: str | None = None, value: Any = None):
        return self.first_where(key, operation, value, or_fail=True)

    def map(self, callback: abc.Callable) -> SequenceBox:
        return self._new(callback(value) for value in self)

    def merge(self, other: abc.Sequence):
        def generator():
            yield from self
            yield from other

        return self._new(generator())

    def average(self) -> numbers.Complex:
        if not self:
            raise ZeroDivisionError

        assert isinstance(the_sum := self.sum(), numbers.Complex)
        return the_sum / len(self)

    def sum(self) -> numbers.Complex | Literal[0]:
        return self.reduce(lambda x, y: x + y)

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

    def where(self, key: str, operation: str | None = None, value: Any = None):
        return self.filter(lambda obj: self._where(obj, key, operation, value))

    def zip(self, other: abc.Sequence):
        return self._new(zip(self, other))


__all__ = ["SequenceBox", "BoxAbstract"]
