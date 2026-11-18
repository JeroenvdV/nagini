# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

import asyncio
from nagini_contracts.contracts import *


async def count(n: int, seen: GInt) -> int:
    Requires(n >= 0)
    Ensures(Result() == n)
    steps: GInt = 0
    i = 0
    while i < n:
        Invariant(0 <= i and i <= n and steps == i)
        await asyncio.sleep(0)
        i += 1
        steps += 1
    return i


async def main() -> int:
    g: GInt = 3
    return await count(3, g)


asyncio.run(main())
