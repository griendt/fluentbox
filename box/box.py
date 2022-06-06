from __future__ import annotations

import collections.abc as abc
import numbers
import operator
from abc import ABC, abstractmethod
from typing import final, Any


class BoxAbstract(ABC, abc.Iterable):
    items: abc.Iterable
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
        if not hasattr(self, "items"):
            self.items = items

    def __contains__(self, obj: object) -> bool:
        return obj in self.items

    def __iter__(self) -> abc.Generator:
        yield from self.items

    @final
    @property
    def item_type(self) -> type:
        return type(self.items)

    def chunk(self, chunk_size: int) -> BoxAbstract:
        def generator() -> abc.Generator:
            chunk = []

            for value in self:
                chunk.append(value)

                if len(chunk) == chunk_size:
                    yield chunk

        return type(self)(generator())

    def diff(self, other: abc.Iterable) -> BoxAbstract:
        return self._new(value for value in self if value not in other)

    def each(self, callback: abc.Callable) -> BoxAbstract:
        for value in self:
            callback(value)

        return self

    def filter(self, callback: abc.Callable | None = None) -> BoxAbstract:
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

    def map(self, callback: abc.Callable) -> BoxAbstract:
        return self._new(callback(value) for value in self)

    def merge(self, other: abc.Iterable) -> BoxAbstract:
        def generator() -> abc.Generator:
            yield from self
            yield from other

        return self._new(generator())

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

    @abstractmethod
    def _new(self, items: abc.Iterable) -> BoxAbstract:
        ...

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

    def where(self, key: str, operation: str | None = None, value: Any = None) -> BoxAbstract:
        return self.filter(lambda obj: self._where(obj, key, operation, value))

    def zip(self, other: abc.Iterable) -> BoxAbstract:
        return self._new(zip(self, other))


class SequenceBox(BoxAbstract, abc.Sequence):
    items: abc.Sequence

    def __init__(self, items: Any):
        super().__init__(items)

        if isinstance(items, abc.Sequence):
            self.items = items

        else:
            self.items = [items]

    def __len__(self) -> int:
        return len(self.items)

    def __getitem__(self, index: int | slice) -> Any:
        return self.items[index]

    @final
    def _new(self, items: abc.Iterable) -> SequenceBox:
        return type(self)(self.item_type(items))

    def chunk(self, chunk_size: int) -> SequenceBox:
        # Using slices is more efficient than using the for-loop implementation in `BoxAbstract`.
        return self._new(self[i: i + chunk_size] for i in range(0, len(self), chunk_size))

    def average(self) -> Any:
        if not len(self):
            raise ZeroDivisionError

        assert isinstance(the_sum := self.sum(), numbers.Complex)
        return the_sum / len(self)
