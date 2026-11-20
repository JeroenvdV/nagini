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


async def work(c: Cell, n: int) -> int:
    Requires(Acc(c.val))
    Requires(MustTerminate(2))
    Ensures(Acc(c.val) and c.val == Old(c.val) + n)
    Ensures(Result() == n * 2)
    c.val = c.val + n
    return n * 2


async def start(c: Cell) -> Task[int]:
    Requires(Acc(c.val) and c.val == 10)
    Ensures(Acc(ThreadPost(Result())))
    Ensures(Joinable(Result()))
    Ensures(getMethod(Result()) == work)
    Ensures(getArg(Result(), 0) is c and getArg(Result(), 1) == 5)
    Ensures(getOld(Result(), arg(0).val) == 10)
    Ensures(WaitLevel() < Level(Result()))
    return create_task(work(c, 5))


async def finish(t: Task[int], c: Cell) -> int:
    Requires(Acc(ThreadPost(t)))
    Requires(getMethod(t) == work)
    Requires(getArg(t, 0) is c and getArg(t, 1) == 5)
    Requires(getOld(t, arg(0).val) == 10)
    Requires(WaitLevel() < Level(t))
    Ensures(Acc(c.val) and c.val == 15)
    Ensures(Result() == 10)
    return await t


async def finish_unknown(t: Task[int], c: Cell) -> int:
    Requires(Acc(ThreadPost(t)))
    Requires(getArg(t, 0) is c)
    Requires(WaitLevel() < Level(t))
    #:: ExpectedOutput(postcondition.violated:assertion.false)
    Ensures(Result() == 10)
    return await t


async def finish_wrong_level(t: Task[int], c: Cell) -> int:
    Requires(Acc(ThreadPost(t)))
    #:: ExpectedOutput(await.failed:wait.level.invalid)
    return await t


async def main() -> int:
    Ensures(Result() == 10)
    c = Cell()
    c.val = 10
    t = await start(c)
    return await finish(t, c)


r = asyncio.run(main())
assert r == 10
