# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

import asyncio
from nagini_contracts.contracts import *


async def f() -> int:
    return 1


def g() -> None:
    #:: ExpectedOutput(invalid.program:asyncio.create_task.outside.async)
    t = asyncio.create_task(f())
