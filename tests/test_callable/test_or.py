from lambdas import _


class _ImplementsOr(object):
    def __or__(self, other: str) -> int:
        return isinstance(other, str) and len(other) or NotImplemented

    def __eq__(self, other: object) -> bool:
        return isinstance(other, _ImplementsOr) or NotImplemented

    def __repr__(self) -> str:
        return 'hello'


class _ImplementsROr(object):
    def __ror__(self, other: int) -> str:
        return isinstance(other, int) and str(other) or NotImplemented

    def __eq__(self, other: object) -> bool:
        return isinstance(other, _ImplementsROr) or NotImplemented

    def __repr__(self) -> str:
        return 'howdy'


def test_to_the_left():
    """Ensures that the OR operator works when used to the left."""
    expr = _ImplementsOr() | _
    assert expr('foo') == 3
    assert repr(expr) == 'hello | _'


def test_to_the_right():
    """Ensures that the OR operator works when used to the right."""
    expr = _ | _ImplementsROr()
    assert expr(99) == '99'
    assert repr(expr) == '_ | howdy'


def test_combinations():
    """Ensures that combinations of OR work correctly."""
    expr = 60 | _ | 6 | 4
    assert expr(4) == 62
    assert repr(expr) == '60 | _ | 6 | 4'
