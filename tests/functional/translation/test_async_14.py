# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from asyncio import create_task
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate
from nagini_contracts.thread import Joinable


async def f() -> int:
    Requires(MustTerminate(2))
    return 1


async def g() -> None:
    #:: ExpectedOutput(invalid.program:asyncio.task.not.awaited)
    t = create_task(f())
    assert t is not None
    Assert(Joinable(t))
