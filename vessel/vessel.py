from __future__ import annotations

import collections.abc as abc
from typing import final


class Vessel:
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

    @final
    def _new(self, items):
        return type(self)(self.item_type(items))

    @final
    @property
    def item_type(self) -> type:
        return type(self._items)

    def all(self) -> abc.Collection:
        return self._items

    def each(self, callback: abc.Callable) -> Vessel:
        for _, value in self.items():
            callback(value)

        return self

    def filter(self, callback: abc.Callable = None) -> Vessel:
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

    def map(self, callback: abc.Callable) -> Vessel:
        if isinstance(self._items, abc.Mapping):
            return self._new({key: callback(value) for key, value in self.items()})

        return self._new([callback(value) for _, value in self.items()])


__all__ = ["Vessel"]
