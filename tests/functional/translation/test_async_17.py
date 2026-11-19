# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

import asyncio
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


async def work(n: int) -> int:
    Requires(MustTerminate(2))
    Ensures(Result() == n)
    return n


async def break_before_await(n: int) -> None:
    i = 0
    while i < n:
        #:: ExpectedOutput(invalid.program:asyncio.task.not.awaited)
        t = asyncio.create_task(work(i))
        if i == 3:
            break
        await t
        i += 1
