# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

import asyncio
from nagini_contracts.contracts import *


async def f() -> int:
    return 1


async def g() -> None:
    #:: ExpectedOutput(unsupported:asyncio.gather with keyword arguments or without coroutines)
    await asyncio.gather(f(), f(), return_exceptions=True)
