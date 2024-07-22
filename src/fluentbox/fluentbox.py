from __future__ import annotations

import collections.abc as abc
import numbers
import operator
import typing
from typing import final, Any, cast, Protocol, runtime_checkable

from frozendict import frozendict


@runtime_checkable
class SizedIterable[T](abc.Sized, abc.Iterable[T], Protocol):
    """Intersection type for `abc.Sized` and `abc.Iterable`."""
    pass


class Box[T](abc.Iterable[T]):
    """Base class for all `Box` types."""

    _items: abc.Iterable[T]
    _OPERATOR_MAPPING: dict[str, abc.Callable[[T, Any], bool]] = {
        "=": operator.eq,
        "==": operator.eq,
        "!=": operator.ne,
        "<>": operator.ne,
        "<=": operator.le,
        ">=": operator.ge,
        "<": operator.lt,
        ">": operator.gt,
    }

    def __init__(self, items: abc.Iterable[T]):
        """
        Instantiate a new Box. Does not evaluate or exhaust the given iterable.

        :param items: The iterable to collect.
        """
        if not hasattr(self, "_items"):
            self._items = items

    def __bool__(self) -> bool:
        """
        Whether the `Box` is considered empty. This is equivalent to whether the underlying items it collects is considered empty.

        :return: Whether the `Box` is considered empty.
        """
        return bool(self._items)

    def __contains__(self, obj: T) -> bool:
        """
        Whether the object is contained in this `Box`.

        :param obj: The object to check.
        :return: Whether the object is in this `Box`.
        """
        return obj in self._items

    def __iter__(self) -> abc.Generator[T]:
        """Loop over the items this `Box` contains. Yields items one by one."""
        yield from self._items

    @final
    @property
    def item_type(self) -> type[T]:
        """
        :return: The underlying iterable type that this `Box` wraps around.
        """
        return type(self._items)

    def all(self) -> abc.Iterable[T]:
        """
        Get the underlying iterable that this `Box` wraps around, effectively unwrapping.
        If the underlying iterable is a generator, it will remain one, and it will not be exhausted.

        :return: The underlying iterable object.
        """
        return self._items

    def chunk(self, chunk_size: int) -> Box[list[T]]:
        """
        Split the items in chunks (each chunk being a list). Each chunk will have the given size, except for (possibly) the last chunk,
        which will have a size between 1 and the given chunk size. A new `Box` is returned containing the chunked items.

        Note that if the underlying iterable is a generator, it will be exhausted!

        :param chunk_size: The chunk size.
        :return: A new `Box` instance containing the chunked items.
        """

        def generator() -> abc.Generator[list[T]]:
            chunk = []

            for value in self:
                chunk.append(value)

                if len(chunk) == chunk_size:
                    yield chunk

        return type(self)(generator())

    def diff(self, other: abc.Iterable) -> Box[T]:
        """
        Create a new `Box` instance, whose items are the items in this `Box` that are not in the other iterable.
        If this `Box` has a generator as its underlying iterable, the new `Box` instance will have a generator as its underlying iterable as well;
        but be aware that exhausting either the original or the resulting generator will also exhaust the other.

        :param other: The other iterable to check against. This may be a `Box` or any other iterable type.
        :return: A new `Box` containing the items that are not in the other iterable.
        """
        return self._new(value for value in self if value not in other)

    def each(self, callback: abc.Callable[[T], Any]) -> Box[T]:
        """
        Apply the callback to each item. If this `Box` contains a generator, it will be exhausted.

        :param callback: The callback to perform on each item.
        :return: The original `Box`.
        """
        for value in self:
            callback(value)

        return self

    def filter(self, callback: abc.Callable[[T], bool] | None = None) -> Box:
        """
        Create a new `Box` instance. The items of this new instance are those in this `Box` that pass the test provided by the callback.
        If no callback is provided, each item will be cast to a `bool` as a test instead.
        If this `Box` has a generator as its underlying iterable, the new `Box` instance will have a generator as its underlying iterable as well;
        but be aware that exhausting either the original or the resulting generator will also exhaust the other.

        :param callback: The test callback.
        :return: A new `Box` containing the values that pass the test.
        """
        if callback is None:
            callback = bool

        return self._new(value for value in self if callback(value))

    def first(self, or_fail: bool = False) -> T | None:
        """
        Get the first item in the `Box`. If the underlying iterable type is not deterministic in its order (e.g. `set`), this method will also not be
        deterministic. If the underlying iterable is a generator, one value will be yielded, and therefore, subsequent calls to `first` will yield another
        value. If the `Box` is empty, then `None` is returned instead, unless `or_fail` is set to `True`, in which case an `IndexError` is thrown.

        :param or_fail: Whether to throw an `IndexError` if no item exists.
        :return: The first element.
        :throws: `IndexError` if no element exists and `or_fail` is `True`.
        """
        for value in self:
            return value

        if or_fail:
            raise IndexError

        return None

    def first_or_fail(self) -> T:
        return self.first(or_fail=True)

    def first_where(self, key: abc.Hashable, operation: str | None = None, value: Any = None, /, or_fail: bool = False) -> T | None:
        """
        Get the first element that satisfies the condition. If no element could be found and `or_fail` is `True`, an `IndexError` is thrown;
        if `or_fail` is `False`, `None` will be returned.

        :param key: The attribute or key of the item to evaluate.
        :param operation: The operation to use when evaluating.
        :param value: The value to evaluate the item's attribute or key against.
        :param or_fail: Whether to throw an `IndexError` or not, if no item satisfying the condition could be found.
        :return: The first item that satisfies the condition.
        :raises IndexError: When no item could be found that satisfies the condition and `or_fail` is `True`.
        """
        for item in self:
            if self._where(item, key, operation, value):
                return item

        if or_fail:
            raise IndexError

        return None

    def first_where_or_fail(self, key: abc.Hashable, operation: str | None = None, value: Any = None) -> T:
        """
        Get the first element that satisfies the condition. If no such item is found, an `IndexError` is thrown.

        :param key: The attribute or key of the item to evaluate.
        :param operation: The operation to use when evaluating.
        :param value: The value to evaluate the item's attribute or key against.
        :return: The first item that satisfies the condition.
        :raises IndexError: When no item could be found that satisfies the condition.
        """
        return self.first_where(key, operation, value, or_fail=True)

    def group_by[TKey: abc.Hashable](self, key: str | abc.Callable[[T], TKey]) -> MutableMappingBox[TKey, list[T]]:
        result: dict[TKey, list[T]] = {}
        callback: abc.Callable[[T], TKey]

        if isinstance(key, str):
            def callback(val):
                return self.__get_attribute_or_key(val, key, raise_on_error=True)

        else:
            callback = key

        for value in self:
            result_key = callback(value)

            if result_key in result:
                result[result_key].append(value)

            else:
                result[result_key] = [value]

        return box(result)

    def key_by[TKey: abc.Hashable](self, key: TKey | abc.Callable[[T], TKey]) -> MutableMappingBox[TKey, T]:
        if isinstance(key, str):
            return self.map_and_key_by(lambda value: (self.__get_attribute_or_key(value, cast(str, key), raise_on_error=True), value))

        return self.map_and_key_by(lambda value: (key(value), value))

    def map[TMapped](self, callback: abc.Callable[[T], TMapped]) -> Box[TMapped]:
        return self._new(callback(value) for value in self)

    def map_and_key_by[TKey: abc.Hashable, TMapped](self, callback: abc.Callable[[T], tuple[TKey, TMapped]]) -> MutableMappingBox[TKey, TMapped]:
        result = {}
        for value in self:
            key, new_value = callback(value)
            result[key] = new_value

        # Preserve MappingBox sub-classing if possible, otherwise, return a fresh MutableMappingBox instance.
        if isinstance(self, MutableMappingBox):
            return self._new(result)

        return box(result)

    def merge[T2](self, other: abc.Iterable[T2]) -> Box[T | T2]:
        def generator() -> abc.Generator:
            yield from self
            yield from other

        return self._new(generator())

    def pipe_into[T2](self, callback: type[T2] | typing.Callable[[typing.Self], T2]) -> T2:
        return callback(self)

    def pluck[TDefault](self, key: abc.Hashable, *, default: TDefault = None, raise_on_error: bool = False) -> Box[T | TDefault]:
        return self.map(lambda item: self.__get_attribute_or_key(item, key, raise_on_error=raise_on_error, default=default))

    def reduce[TInitial, T2](self, callback: abc.Callable[[T | TInitial, T], T2], initial_value: TInitial = None) -> T2:
        result: TInitial | T | T2 = initial_value
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

    def _new[TValue](self, items: abc.Iterable[TValue]) -> typing.Self:
        return type(self)(self.item_type(items))

    @typing.overload
    def _where[TKey: abc.Hashable, TValue](self, obj: abc.Mapping[TKey, TValue], key: TKey, operation: str | None = None, value: Any = None) -> bool:
        ...

    @typing.overload
    def _where(self, obj: object, key: str, operation: str | None = None, value: Any = None) -> bool:
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

    def where(self, key: abc.Hashable, operation: str | None = None, value: Any = None) -> Box[T]:
        return self.filter(lambda obj: self._where(obj, key, operation, value))

    def zip[T2](self, other: abc.Iterable[T2]) -> Box[tuple[T, T2]]:
        return self._new(zip(self, other))

    @staticmethod
    @typing.overload
    def __get_attribute_or_key[TKey: abc.Hashable, TValue, TDefault](obj: abc.Mapping[TKey, TValue], key: TKey, *, raise_on_error: bool = False, default: TDefault = None) -> TValue | TDefault:
        ...

    @staticmethod
    @typing.overload
    def __get_attribute_or_key(obj: object, key: str, *, raise_on_error: bool = False, default: Any = None) -> Any:
        ...

    @staticmethod
    def __get_attribute_or_key(obj: object, key: str, *, raise_on_error: bool = False, default: Any = None) -> Any:
        if hasattr(obj, key):
            return getattr(obj, key)

        elif isinstance(obj, abc.Mapping) and key in obj.keys():
            return obj[key]

        if raise_on_error:
            raise KeyError("Object of type {} does not have key or attribute {}".format(type(obj), key))

        return default


class SizedBox[T](abc.Sized, Box):
    _items: SizedIterable[T]

    def all(self) -> SizedIterable[T]:
        return self._items

    def __len__(self) -> int:
        return len(self._items)

    def average(self) -> Any:
        if not self:
            raise ZeroDivisionError

        assert isinstance(the_sum := self.sum(), numbers.Complex)
        return the_sum / len(self)


class SequenceBox[T](SizedBox, abc.Sequence[T]):
    _items: abc.Sequence

    def __init__(self, items: T | abc.Sequence[T]):
        super().__init__(items)

        if isinstance(items, abc.Sequence):
            self._items = items

        else:
            self._items = [items]

    def _new(self, items: abc.Iterable[T]) -> SequenceBox[T]:
        return cast(SequenceBox, super()._new(items))

    @typing.overload
    def __getitem__(self, index: int) -> T:
        ...

    @typing.overload
    def __getitem__(self, index: slice) -> slice:
        ...

    def __getitem__(self, index: T | slice) -> T | slice:
        return self._items[index]

    def all(self) -> abc.Sequence[T]:
        return self._items

    def chunk(self, chunk_size: int) -> SequenceBox[abc.Iterable[T]]:
        # Using slices is more efficient than using the for-loop implementation in `Box`.
        return self._new(self[i: i + chunk_size] for i in range(0, len(self), chunk_size))

    def reverse(self) -> SequenceBox[T]:
        return self._new(reversed(self))


class MappingBox[TKey: abc.Hashable, TValue](SizedBox, abc.Mapping[TKey, TValue]):
    _items: abc.Mapping

    def __getitem__(self, key: TKey) -> TValue:
        return self._items[key]

    def all(self) -> abc.Mapping[TKey, TValue]:
        return self._items

    def filter(self, callback: abc.Callable[[TKey, TValue], bool] | None = None) -> MappingBox[TKey, TValue]:
        if callback is None:
            # noinspection PyUnusedLocal
            def callback(key: TKey, value: TValue) -> bool:
                return bool(value)

        return cast(MappingBox, self._new({key: value for key, value in self.items() if callback(key, value)}))

    def only(self, keys: abc.Iterable[abc.Hashable]) -> MappingBox:
        # noinspection PyUnusedLocal
        def callback(key: abc.Hashable, value: Any) -> bool:
            return key in keys

        return self.filter(callback)


class MutableMappingBox[TKey: abc.Hashable, TValue](MappingBox[TKey, TValue], abc.MutableMapping[TKey, TValue]):
    _items: abc.MutableMapping

    def __setitem__(self, key: TKey, value: TValue) -> None:
        self._items[key] = value

    def __delitem__(self, key: TKey) -> None:
        del self._items[key]

    def all(self) -> abc.MutableMapping[TKey, TValue]:
        return self._items


class MutableSetBox[TValue](SizedBox, abc.MutableSet, set):
    _items: abc.MutableSet

    def all(self) -> abc.MutableSet[TValue]:
        return self._items

    def add(self, value: TValue) -> None:
        self._items.add(value)

    def discard(self, value: TValue) -> None:
        self._items.discard(value)


@typing.overload
def box(items: None) -> SequenceBox[list]:
    ...


@typing.overload
def box[T: abc.Hashable](items: abc.MutableSet[T]) -> MutableSetBox[T]:
    ...


@typing.overload
def box[TKey: abc.Hashable, TValue](items: abc.MutableMapping[TKey, TValue]) -> MutableMappingBox[TKey, TValue]:
    ...


@typing.overload
def box[TKey: abc.Hashable, TValue](items: abc.Mapping[TKey, TValue]) -> MappingBox[TKey, TValue]:
    ...


@typing.overload
def box[T](items: abc.Sequence[T]) -> SequenceBox[T]:
    ...


@typing.overload
def box[T](items: SizedIterable[T]) -> SizedBox[T]:
    ...


def box(items=None):
    if items is None:
        return box([])

    if not isinstance(items, abc.Iterable):
        return box([items])

    if isinstance(items, abc.MutableSet):
        return MutableSetBox(set(items))

    if isinstance(items, abc.MutableMapping):
        return MutableMappingBox(dict(items))

    if isinstance(items, abc.Mapping):
        return MappingBox(frozendict(items))  # type: ignore

    if isinstance(items, abc.Sequence):
        return SequenceBox(list(items))

    if isinstance(items, SizedIterable):
        return SizedBox(list(items))

    raise TypeError("Cannot create Box instance from item type {}".format(type(items)))


if __name__ == "__main__":
    bx = box({1: 2, 3: 4, 5: 6})

    by = bx.pipe_into(set)
