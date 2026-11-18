# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

import asyncio
from nagini_contracts.contracts import *


async def f() -> int:
    return 1


def g() -> None:
    #:: ExpectedOutput(unsupported:Unsupported asyncio function: ensure_future)
    asyncio.ensure_future(f())
