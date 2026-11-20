# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *


class Cell:
    def __init__(self) -> None:
        self.val = 0
        Ensures(Acc(self.val) and self.val == 0)


def set_val(c: Cell, v: int) -> None:
    Requires(Acc(c.val))
    Ensures(Acc(c.val) and c.val == v)
    c.val = v


def forward(c: Cell) -> None:
    Requires(Acc(c.val))
    Ensures(Acc(c.val) and c.val == 3)
    return set_val(c, 3)


async def aset_val(c: Cell, v: int) -> None:
    Requires(Acc(c.val))
    Ensures(Acc(c.val) and c.val == v)
    c.val = v


async def aforward(c: Cell) -> None:
    Requires(Acc(c.val))
    #:: ExpectedOutput(postcondition.violated:assertion.false)
    Ensures(Acc(c.val) and c.val == 4)
    return await aset_val(c, 3)
