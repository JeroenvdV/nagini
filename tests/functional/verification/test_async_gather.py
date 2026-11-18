# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

import asyncio
from asyncio import gather
from typing import Tuple
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


class Cell:
    def __init__(self) -> None:
        Requires(MustTerminate(1))
        self.val = 0
        Ensures(Acc(self.val) and self.val == 0)

    async def bump(self) -> None:
        Requires(Acc(self.val))
        Requires(MustTerminate(2))
        Ensures(Acc(self.val) and self.val == Old(self.val) + 1)
        self.val += 1


async def work(c: Cell, n: int) -> int:
    Requires(Acc(c.val))
    Requires(MustTerminate(2))
    Ensures(Acc(c.val) and c.val == Old(c.val) + n)
    Ensures(Result() == n * 2)
    await asyncio.sleep(0)
    c.val = c.val + n
    return n * 2


async def read(c: Cell) -> int:
    Requires(Acc(c.val, 1/4))
    Requires(MustTerminate(2))
    Ensures(Acc(c.val, 1/4) and Result() == c.val)
    return c.val


async def forever(c: Cell) -> int:
    Requires(Acc(c.val))
    while True:
        Invariant(Acc(c.val))
        c.val += 1
        await asyncio.sleep(0)
    return 0


async def two_coroutines() -> int:
    Ensures(Result() == 14)
    a = Cell()
    b = Cell()
    r1, r2 = await asyncio.gather(work(a, 3), work(b, 4))
    assert a.val == 3 and b.val == 4
    return r1 + r2


async def tuple_result() -> Tuple[int, None, int]:
    Ensures(Result()[0] == 2 and Result()[2] == 0)
    a = Cell()
    b = Cell()
    c = Cell()
    res = await gather(work(a, 1), b.bump(), read(c))
    assert b.val == 1
    #:: ExpectedOutput(assert.failed:assertion.false)
    assert a.val == 0
    return res


async def overlapping(a: Cell) -> None:
    Requires(Acc(a.val))
    #:: ExpectedOutput(task.creation.failed:insufficient.permission)
    await gather(read(a), work(a, 1))


async def shared_read(a: Cell) -> None:
    Requires(Acc(a.val) and a.val == 5)
    Ensures(Acc(a.val) and a.val == 5)
    x, y = await gather(read(a), read(a))
    assert x == 5 and y == 5
    #:: ExpectedOutput(assert.failed:assertion.false)
    assert x == 6


async def same_cell() -> None:
    a = Cell()
    #:: ExpectedOutput(task.creation.failed:insufficient.permission)
    await gather(work(a, 1), work(a, 2))


async def missing_permission(a: Cell) -> None:
    #:: ExpectedOutput(task.creation.failed:insufficient.permission)
    await gather(work(a, 1))


async def not_terminating() -> None:
    a = Cell()
    b = Cell()
    #:: ExpectedOutput(await.failed:task.not.joinable)
    await gather(work(a, 1), forever(b))
