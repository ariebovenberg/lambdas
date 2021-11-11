from lambdas import _


class _ImplementsAnd(object):
    def __and__(self, other: str) -> int:
        return isinstance(other, str) and len(other) or NotImplemented

    def __eq__(self, other: object) -> bool:
        return isinstance(other, _ImplementsAnd) or NotImplemented

    def __repr__(self) -> str:
        return 'hello'


class _ImplementsRAnd(object):

    def __rand__(self, other: int) -> str:
        return isinstance(other, int) and str(other) or NotImplemented

    def __eq__(self, other: object) -> bool:
        return isinstance(other, _ImplementsRAnd) or NotImplemented

    def __repr__(self) -> str:
        return 'howdy'


def test_to_the_left():
    """Ensures that the AND operator works when used to the left."""
    expr = _ImplementsAnd() & _
    assert expr('foo') == 3
    assert repr(expr) == 'hello & _'


def test_to_the_right():
    """Ensures that the AND operator works when used to the right."""
    expr = _ & _ImplementsRAnd()
    assert expr(99) == '99'
    assert repr(expr) == '_ & howdy'


def test_combinations():
    """Ensures that combinations of AND work correctly."""
    expr = 60 & _ & 5 & 7
    assert expr(7) == 4
    assert repr(expr) == '60 & _ & 5 & 7'
