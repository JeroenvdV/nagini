# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *


def find(k: int) -> tuple[str, int] | None:
    Ensures(Implies(k < 0, Result() is None))
    Ensures(Implies(k >= 0, Result() is not None))
    if k < 0:
        return None
    return ("a", k)


def use(k: int | None) -> int:
    if k is None:
        return -1
    r = find(k)
    if r is None:
        return -1
    name, v = r
    return v


def check(k: int | str | None) -> int:
    #:: ExpectedOutput(postcondition.violated:assertion.false)
    Ensures(Result() >= 0)
    if isinstance(k, int):
        return k
    return 0
