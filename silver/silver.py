from __future__ import annotations

import collections.abc as abc

from typing_extensions import Self  # type: ignore


class Silver:
    _items: abc.Collection

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

    def all(self) -> abc.Collection:
        return self._items

    def each(self, callback: abc.Callable) -> Self:
        for _, value in self.items():
            callback(value)

        return self

    def filter(self, callback: abc.Callable = None) -> Self:
        new_items = type(self._items)()

        if callback is None:
            callback = bool

        if isinstance(new_items, abc.MutableMapping):
            for key, value in self.items():
                if callback(value):
                    new_items[key] = value

        elif isinstance(new_items, abc.MutableSequence):
            for _, value in self.items():
                if callback(value):
                    new_items.append(value)

        elif isinstance(new_items, abc.MutableSet):
            for _, value in self.items():
                if callback(value):
                    new_items.add(value)

        else:
            raise TypeError(f"Item type {type(self._items)} should be Mutable")

        return type(self)(new_items)

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

        elif isinstance(self._items, abc.Iterable):
            for key, value in enumerate(self._items):
                yield key, value

    def map(self, callback: abc.Callable) -> Self:
        new_items = type(self._items)()

        if isinstance(new_items, abc.MutableMapping):
            for key, value in self.items():
                new_items[key] = callback(value)

        elif isinstance(new_items, abc.MutableSequence):
            for _, value in self.items():
                new_items.append(callback(value))

        elif isinstance(new_items, abc.MutableSet):
            for _, value in self.items():
                new_items.add(callback(value))

        return type(self)(new_items)
