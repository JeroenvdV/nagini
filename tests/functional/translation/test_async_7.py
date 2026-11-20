# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

import asyncio
from nagini_contracts.contracts import *


class NegativeError(Exception):
    pass


async def f(x: int) -> int:
    Exsures(NegativeError, True)
    if x < 0:
        raise NegativeError()
    return x


async def g() -> None:
    #:: ExpectedOutput(unsupported:Task coroutines must not be class methods or raise exceptions and must not mention WaitLevel in their postconditions.)
    t = asyncio.create_task(f(1))
    await t
