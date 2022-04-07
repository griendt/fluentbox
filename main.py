from __future__ import annotations

import collections.abc
from typing import Callable, Generator, Sequence


class Collection:
    _items: collections.abc.Collection

    def __init__(self, items: collections.abc.Collection):
        self._items = items

    def __contains__(self, obj: object) -> bool:
        return obj in self._items

    def __len__(self) -> int:
        return len(self._items)

    def __iter__(self):
        if isinstance(self._items, dict):
            for key, value in self._items.items():
                yield key, value

        for value in self._items:
            yield value

    def all(self):
        if isinstance(self._items, Generator):
            return self.do().all()

        return self._items

    def do(self) -> Collection:
        # Exhaust any underlying Generator by casting it to its appropriate item type
        return type(self)(type(self._items)(self._items))

    def each(self, callback: Callable):
        def generator(obj):
            for item in obj:
                callback(item)
                yield item

        return type(self)(generator(self))

    def first(self, or_fail: bool = False):
        for item in self:
            return item

        if or_fail:
            raise IndexError

    def first_or_fail(self):
        return self.first(or_fail=True)

    def items(self):
        if isinstance(self._items, dict):
            for key, value in self._items.items():
                yield key, value

        elif isinstance(self._items, Sequence):
            for key, value in enumerate(self._items):
                yield key, value

        else:
            raise ValueError(f"Item type {self._item_type} is not a dict nor implements Sequence")

    def map(self, callback: Callable) -> Collection:
        def generator(obj):
            for item in obj:
                yield callback(item)

        return type(self)(generator(self))

    def filter(self, callback: Callable = None):
        def generator(obj):
            for item in obj:
                if callback is None:
                    if item:
                        yield item
                elif callback(item):
                    yield item

        return type(self)(generator(self))

    def to(self, cls: type):
        return cls(self._items)


def collection_of(cls: type) -> type:
    if not issubclass(cls, collections.abc.Collection):
        raise TypeError(f"Cannot make concrete Collection class of type {cls}")

    collection_cls = Collection
    collection_cls.__name__ = cls.__name__ + "Collection"
    collection_cls.__annotations__["_items"] = cls
    collection_cls._item_type = cls

    return collection_cls


def collect(*args):
    if len(args) > 1:
        return Collection(args)

    if isinstance(args[0], list):
        return Collection(args[0])

    return Collection(list(args))


if __name__ == '__main__':
    x = (Collection({3, 4, 5})
         .map(lambda i: ((i := i + 1), (i + 2))[-1])
         .filter(lambda item: item < 30)
         .each(lambda i: print(f"I am {i}!"))
         .do()
         )

    print(x._items)
