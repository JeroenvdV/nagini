# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

import asyncio
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


async def work(n: int) -> int:
    Requires(MustTerminate(2))
    Ensures(Result() == n)
    return n


async def raise_before_await(fail: bool) -> int:
    #:: ExpectedOutput(invalid.program:asyncio.task.not.awaited)
    t = asyncio.create_task(work(1))
    if fail:
        raise ValueError()
    return await t
