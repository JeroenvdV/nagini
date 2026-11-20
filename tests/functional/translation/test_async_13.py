# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

import asyncio
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


async def f() -> int:
    Requires(MustTerminate(2))
    return 1


async def g() -> None:
    #:: ExpectedOutput(invalid.program:asyncio.task.not.awaited)
    asyncio.create_task(f())
