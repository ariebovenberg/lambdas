# -*- coding: utf-8 -*-

import abc
import operator
from functools import partial, reduce
from typing import Callable, Generic, List, Mapping, TypeVar, Union, cast

from typing_extensions import Protocol

T1 = TypeVar('T1')
T2 = TypeVar('T2')
T3 = TypeVar('T3')
T_co = TypeVar('T_co', covariant=True)
T_contra = TypeVar('T_contra', contravariant=True)

_Number = Union[int, float, complex]


def _fmap(callback):  # pragma: nocover
    # TODO: Remove `pragma` after https://github.com/dry-python/lambdas/issues/4
    """Convers callback to instance method with two arguments."""
    def decorator(self, second):
        return lambda first: callback(first, second)
    return decorator


def _unary_fmap(callback):
    """Convers callback to unary instance method."""
    def decorator(self):
        return callback
    return decorator


def _flip(callback):
    """Flips arguments: the first one becomes the second."""
    return lambda first, second: callback(second, first)


class _LambdaDynamicProtocol(Protocol[T1]):
    """
    This is one of the most complicated parts in this library.

    This is a generic protocol definition that works fine,
    except it cannot change the field name in runtime.

    And we need this field name to change when we call ``_.some``.
    When this happens we use our ``mypy`` plugin
    to change the field name from ``lambdas_generic_field`` to ``some``.

    And it continues to work as is.
    """

    lambdas_generic_field: T1


class _MathExpression(object):  # noqa: WPS214
    """
    Mathmatical expression callable class.

    This class helps us to build an callable with complex mathematical
    expression, basically it's the substitute of `x` in a expression.
    When we call this class the number passed trought the instance will be
    the `x`.

    See the example below:

        >>> from lambdas import _MathExpression
        >>> complex_expression = (10 ** 2) / _MathExpression() * 10
        >>> complex_expression(2)
        500.0

    """

    def __init__(self) -> None:
        self._operations: List[Callable[[_Number], _Number]] = []

    def __call__(self, number: _Number) -> _Number:
        first_operation, *rest_of_the_operations = self._operations
        return reduce(
            lambda partial_result, operation: operation(partial_result),
            rest_of_the_operations,
            first_operation(number),
        )

    def __add__(self, other: _Number) -> '_MathExpression':
        return self._add_operation(_flip(operator.add), other)

    def __sub__(self, other: _Number) -> '_MathExpression':
        return self._add_operation(_flip(operator.sub), other)

    def __mul__(self, other: _Number) -> '_MathExpression':
        return self._add_operation(_flip(operator.mul), other)

    def __floordiv__(self, other: _Number) -> '_MathExpression':
        return self._add_operation(_flip(operator.floordiv), other)

    def __truediv__(self, other: _Number) -> '_MathExpression':
        return self._add_operation(_flip(operator.truediv), other)

    def __mod__(self, other: _Number) -> '_MathExpression':
        return self._add_operation(_flip(operator.mod), other)

    def __pow__(self, other: _Number) -> '_MathExpression':
        return self._add_operation(_flip(operator.pow), other)

    def __radd__(self, other: _Number) -> '_MathExpression':
        return self._add_operation(operator.add, other)

    def __rsub__(self, other: _Number) -> '_MathExpression':
        return self._add_operation(operator.sub, other)

    def __rmul__(self, other: _Number) -> '_MathExpression':
        return self._add_operation(operator.mul, other)

    def __rfloordiv__(self, other: _Number) -> '_MathExpression':
        return self._add_operation(operator.floordiv, other)

    def __rtruediv__(self, other: _Number) -> '_MathExpression':
        return self._add_operation(operator.truediv, other)

    def __rmod__(self, other: _Number) -> '_MathExpression':
        return self._add_operation(operator.mod, other)

    def __rpow__(self, other: _Number) -> '_MathExpression':
        return self._add_operation(operator.pow, other)

    def _add_operation(
        self,
        operation: Callable[[_Number, _Number], _Number],
        other: _Number,
    ) -> '_MathExpression':
        self._operations.append(partial(operation, other))
        return self


class _SupportsAnd(Protocol[T_contra, T_co]):
    def __and__(self, other: T_contra) -> T_co:  # pragma: no cover
        ...  # noqa: WPS428


class _SupportsRAnd(Protocol[T_contra, T_co]):
    def __rand__(self, other: T_contra) -> T_co:  # pragma: no cover
        ...  # noqa: WPS428


class _SupportsOr(Protocol[T_contra, T_co]):
    def __or__(self, other: T_contra) -> T_co:  # pragma: no cover
        ...  # noqa: WPS428


class _SupportsROr(Protocol[T_contra, T_co]):
    def __ror__(self, other: T_contra) -> T_co:  # pragma: no cover
        ...  # noqa: WPS428


class _Operation(Generic[T1, T2]):
    """A unary operation."""

    @abc.abstractmethod
    def __call__(self, __arg: T1) -> T2:  # noqa: WPS112
        """Apply the operation to a given input."""

    @property
    @abc.abstractmethod
    def precedence(self) -> int:
        """Precedence of the operation where 0 is the highest precedence.

        According to:
        docs.python.org/3/reference/expressions.html#operator-precedence
        """

    def as_string(self, inner: str) -> str:
        """Construct a visual representation of the operation."""


class _SomethingAnd(_Operation[T1, T2]):
    """The operation `<operand> & <argument>`."""

    precedence = 8

    def __init__(self, operand: _SupportsAnd[T1, T2]) -> None:
        self.operand = operand

    def __call__(self, __arg: T1) -> T2:  # noqa: WPS112
        return self.operand & __arg

    def as_string(self, inner: str) -> str:
        return '{0.operand!r} & {1}'.format(self, inner)


class _AndSomething(_Operation[T1, T2]):
    """The operation `<argument> & <operand>`."""

    precedence = 8

    def __init__(self, operand: _SupportsRAnd[T1, T2]) -> None:
        self.operand = operand

    def __call__(self, __arg: T1) -> T2:  # noqa: WPS112
        return __arg & self.operand

    def as_string(self, inner: str) -> str:
        return '{0} & {1.operand!r}'.format(inner, self)


class _SomethingOr(_Operation[T1, T2]):
    """The operation `<operand> | <argument>`."""

    precedence = 10

    def __init__(self, operand: _SupportsOr[T1, T2]) -> None:
        self.operand = operand

    def __call__(self, __arg: T1) -> T2:  # noqa: WPS112
        return self.operand | __arg

    def as_string(self, inner: str) -> str:
        return '{0.operand!r} | {1}'.format(self, inner)


class _OrSomething(_Operation[T1, T2]):
    """The operation `<argument> | <operand>`."""

    precedence = 10

    def __init__(self, operand: _SupportsROr[T1, T2]) -> None:
        self.operand = operand

    def __call__(self, __arg: T1) -> T2:  # noqa: WPS112
        return __arg | self.operand

    def as_string(self, inner: str) -> str:
        return '{0} | {1.operand!r}'.format(inner, self)


class _Expression(Generic[T1, T2]):

    @abc.abstractmethod
    def __call__(self, __arg: T1) -> T2:  # noqa: WPS112
        """Apply the expression to a given input."""

    # dunder naming so it doesn't conflict with __getattr__ behavior
    @abc.abstractmethod
    def __precedence__(self) -> int:
        """The precedence of this expression (0=highest)."""

    def __and__(self, other: _SupportsRAnd[T2, T3]) -> '_Expression[T1, T3]':
        return _Chain(self, _AndSomething(other))

    # mypy warns that this method and the matching magic method of its argument
    # overlap. We do handle this correctly, but mypy cannot infer this.
    def __rand__(  # type: ignore[misc]
        self, other: _SupportsAnd[T2, T3],
    ) -> '_Expression[T1, T3]':
        return _Chain(self, _SomethingAnd(other))

    def __or__(self, other: _SupportsROr[T2, T3]) -> '_Expression[T1, T3]':
        return _Chain(self, _OrSomething(other))

    # mypy warns that this method and the matching magic method of its argument
    # overlap. We do handle this correctly, but mypy cannot infer this.
    def __ror__(  # type: ignore[misc]
        self, other: _SupportsOr[T2, T3],
    ) -> '_Expression[T1, T3]':
        return _Chain(self, _SomethingOr(other))

    # TODO: add all magic methods from _Callable here


class _Chain(Generic[T1, T2, T3], _Expression[T1, T3]):
    # Dunder naming is ugly, but it's the only way to prevent
    # conflicts with __getattr__ behavior
    __previous__: _Expression[T1, T2]
    __operation__: _Operation[T2, T3]

    def __init__(
        self, previous: _Expression[T1, T2], operation: _Operation[T2, T3],
    ) -> None:
        self.__previous__ = previous
        self.__operation__ = operation

    def __call__(self, __arg: T1) -> T3:  # noqa: WPS112
        return self.__operation__(self.__previous__(__arg))

    def __repr__(self) -> str:
        return self.__operation__.as_string(
            repr(self.__previous__)
            if self.__previous__.__precedence__()  # noqa: WPS609
            <= self.__operation__.precedence  # noqa: W503
            else '({0!r})'.format(self.__previous__),
        )

    def __precedence__(self) -> int:
        return self.__operation__.precedence


class _Callable(_Expression[T1, T1]):  # noqa: WPS214
    """
    Short lambda implementation.

    It is useful when you have
    a lot of single-argument ``lambda`` functions here and there.

    It can be used like so:

        >>> from lambdas import _
        >>> response = [{'count': 3}, {'count': 1}, {'count': 2}]
        >>> sorted(response, key=_['count'])
        [{'count': 1}, {'count': 2}, {'count': 3}]

    """

    def __call__(self, __arg: T2) -> T2:  # noqa: WPS112
        return __arg

    def __and__(self, other: _SupportsRAnd[T2, T3]) -> '_Expression[T2, T3]':
        return super(  # noqa: WPS608
            _Callable, cast(_Callable[T2], self),
        ).__and__(other)

    # mypy warns that this method and the matching magic method of its argument
    # overlap. We do handle this correctly, but mypy cannot infer this.
    def __rand__(  # type: ignore[misc]
        self, other: _SupportsAnd[T2, T3],
    ) -> '_Expression[T2, T3]':
        return super(  # noqa: WPS608
            _Callable, cast(_Callable[T2], self),
        ).__rand__(other)

    def __or__(self, other: _SupportsROr[T2, T3]) -> '_Expression[T2, T3]':
        return super(  # noqa: WPS608
            _Callable, cast(_Callable[T2], self),
        ).__or__(other)

    # mypy warns that this method and the matching magic method of its argument
    # overlap. We do handle this correctly, but mypy cannot infer this.
    def __ror__(  # type: ignore[misc]
        self, other: _SupportsOr[T2, T3],
    ) -> '_Expression[T2, T3]':
        return super(  # noqa: WPS608
            _Callable, cast(_Callable[T2], self),
        ).__ror__(other)

    def __repr__(self) -> str:
        return '_'

    def __precedence__(self) -> int:
        return 0

    def __getattr__(
        self,
        key: str,
    ) -> Callable[[_LambdaDynamicProtocol[T2]], T2]:
        return operator.attrgetter(key)

    def __getitem__(
        self, key: T2,
    ) -> Callable[[Mapping[T2, T3]], T3]:
        return operator.itemgetter(key)

    def __add__(self, other: _Number) -> _MathExpression:
        return _MathExpression() + other

    def __sub__(self, other: _Number) -> _MathExpression:
        return _MathExpression() - other

    def __mul__(self, other: _Number) -> _MathExpression:
        return _MathExpression() * other

    def __floordiv__(self, other: _Number) -> _MathExpression:
        return _MathExpression() // other

    def __truediv__(self, other: _Number) -> _MathExpression:
        return _MathExpression() / other

    def __mod__(self, other: _Number) -> _MathExpression:
        return _MathExpression() % other

    def __pow__(self, other: _Number) -> _MathExpression:
        return _MathExpression() ** other

    def __radd__(self, other: _Number) -> _MathExpression:
        return other + _MathExpression()

    def __rsub__(self, other: _Number) -> _MathExpression:
        return other - _MathExpression()

    def __rmul__(self, other: _Number) -> _MathExpression:
        return other * _MathExpression()

    def __rfloordiv__(self, other: _Number) -> _MathExpression:
        return other // _MathExpression()

    def __rtruediv__(self, other: _Number) -> _MathExpression:
        return other / _MathExpression()

    def __rmod__(self, other: _Number) -> _MathExpression:
        return other % _MathExpression()  # noqa: S001

    def __rpow__(self, other: _Number) -> _MathExpression:
        return other ** _MathExpression()

    __xor__: Callable[['_Callable', T1], Callable[[T1], T1]] = _fmap(  # type: ignore  # noqa
        operator.xor,
    )
    __divmod__: Callable[['_Callable', T1], Callable[[T1], T1]] = _fmap(divmod)  # type: ignore  # noqa

    __lshift__: Callable[['_Callable', T1], Callable[[T1], T1]] = _fmap(  # type: ignore  # noqa
        operator.lshift,
    )
    __rshift__: Callable[['_Callable', T1], Callable[[T1], T1]] = _fmap(  # type: ignore  # noqa
        operator.rshift,
    )

    __lt__: Callable[['_Callable', T1], Callable[[T1], T1]] = _fmap(  # type: ignore  # noqa
        operator.lt,
    )
    __le__: Callable[['_Callable', T1], Callable[[T1], T1]] = _fmap(  # type: ignore  # noqa
        operator.le,
    )
    __gt__: Callable[['_Callable', T1], Callable[[T1], T1]] = _fmap(  # type: ignore  # noqa
        operator.gt,
    )
    __ge__: Callable[['_Callable', T1], Callable[[T1], T1]] = _fmap(  # type: ignore  # noqa
        operator.ge,
    )
    __eq__: Callable[  # type: ignore
        ['_Callable', object], Callable[[object], bool],
    ] = _fmap(  # type: ignore
        operator.eq,
    )
    __ne__: Callable[  # type: ignore
        ['_Callable', object], Callable[[object], bool],
    ] = _fmap(  # type: ignore
        operator.ne,
    )

    __neg__: Callable[['_Callable'], Callable[[T1], T1]] = _unary_fmap(  # type: ignore  # noqa
        operator.neg,
    )
    __pos__: Callable[['_Callable'], Callable[[T1], T1]] = _unary_fmap(  # type: ignore  # noqa
        operator.pos,
    )
    __invert__: Callable[['_Callable'], Callable[[T1], T1]] = _unary_fmap(  # type: ignore  # noqa
        operator.invert,
    )

    __rdivmod__: Callable[['_Callable', T1], Callable[[T1], T1]] = _fmap(  # type: ignore  # noqa
        _flip(divmod),
    )

    __rlshift__: Callable[['_Callable', T1], Callable[[T1], T1]] = _fmap(  # type: ignore  # noqa
        _flip(operator.lshift),
    )
    __rrshift__: Callable[['_Callable', T1], Callable[[T1], T1]] = _fmap(  # type: ignore  # noqa
        _flip(operator.rshift),
    )

    __rxor__: Callable[['_Callable', T1], Callable[[T1], T1]] = _fmap(  # type: ignore  # noqa
        _flip(operator.xor),
    )


#: Our main alias for the lambda object:
_ = _Callable()  # type: ignore # noqa: WPS122
