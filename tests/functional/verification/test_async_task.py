# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

import asyncio
from asyncio import Task, create_task
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate, WaitLevel, Level
from nagini_contracts.thread import ThreadPost, getArg, getMethod, getOld, arg, Joinable


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


async def forever(c: Cell) -> int:
    Requires(Acc(c.val))
    while True:
        Invariant(Acc(c.val))
        c.val += 1
        await asyncio.sleep(0)
    return 0


async def two_tasks() -> int:
    Ensures(Result() == 14)
    a = Cell()
    b = Cell()
    t1 = asyncio.create_task(work(a, 3))
    t2 = create_task(work(b, 4))
    r1 = await t1
    r2 = await t2
    assert a.val == 3 and b.val == 4
    return r1 + r2


async def task_owns_permission() -> None:
    a = Cell()
    t = create_task(work(a, 3))
    #:: ExpectedOutput(assignment.failed:insufficient.permission)
    a.val = 5


async def missing_permission(a: Cell) -> None:
    #:: ExpectedOutput(task.creation.failed:insufficient.permission)
    t = create_task(work(a, 3))


async def method_task() -> None:
    c = Cell()
    t = create_task(c.bump())
    await t
    assert c.val == 1
    await t
    assert c.val == 1


async def await_twice() -> None:
    c = Cell()
    t = create_task(work(c, 3))
    x = await t
    y = await t
    assert x == 6
    #:: ExpectedOutput(assert.failed:assertion.false)
    assert y == 6


async def not_terminating() -> None:
    a = Cell()
    t = create_task(forever(a))
    #:: ExpectedOutput(await.failed:task.not.joinable)
    x = await t
