# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from asyncio import Task, create_task
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


async def work(n: int) -> int:
    Requires(MustTerminate(2))
    Ensures(Result() == n)
    return n


async def awaited_on_both_branches(early: bool) -> int:
    Ensures(Result() == 1)
    t = create_task(work(1))
    if early:
        r = await t
        return r
    return await t


async def awaited_in_loop(n: int) -> int:
    Requires(n >= 0)
    Ensures(Result() == n)
    i = 0
    while i < n:
        Invariant(0 <= i and i <= n)
        t = create_task(work(i))
        r = await t
        i += 1
    return i


async def awaited_after_caught_exception(fail: bool) -> int:
    Ensures(Result() == 2)
    t = create_task(work(2))
    try:
        if fail:
            raise ValueError()
    except ValueError:
        pass
    return await t


async def handed_on(early: bool) -> Task[int]:
    t = create_task(work(3))
    if early:
        return t
    await t
    return t


async def wrong_result() -> int:
    #:: ExpectedOutput(postcondition.violated:assertion.false)
    Ensures(Result() == 1)
    t = create_task(work(2))
    r = await t
    return r
