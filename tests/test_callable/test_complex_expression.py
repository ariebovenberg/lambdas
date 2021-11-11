# -*- coding: utf-8 -*-

import math
from typing import Iterable, List

from lambdas import _


def test_empty():
    """Ensures that empty expressions act correctly."""
    assert _(8) == 8
    assert repr(_) == '_'


def test_operator_precedence():
    """Ensure operator precedence works correctly."""
    expr = (9 | _) & 6 & 7
    assert expr(3) == 2
    assert repr(expr) == '(9 | _) & 6 & 7'

    expr2 = 9 | (_ & 6) & 7
    assert expr2(3) == 11
    assert repr(expr2) == '9 | _ & 6 & 7'


def test_complex_overloads():
    """Ensure complex overloads work correctly."""
    expr = _Test0() | _ & _Test1() & _Test2() | _Test3()
    assert math.isclose(expr(939), 2)


def test_complex_expression():
    """Ensures that add works correctly."""
    complex_expression = ((10 ** 5) / (_ % 3) * 9)
    assert math.isclose(complex_expression(5), 450000.0)  # type: ignore


class _Test0(object):
    def __or__(self, arg: List[str]) -> List[bool]:
        if isinstance(arg, list):
            return list(map(bool, map(int, arg)))
        return NotImplemented


class _Test1(object):
    def __rand__(self, arg: int) -> str:
        return str(arg) * 2


class _Test2(object):
    def __rand__(self, arg: str) -> List[str]:
        return list(arg)


class _Test3(object):
    def __ror__(self, arg: Iterable[int]) -> float:
        return sum(arg) / 3
