# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

import asyncio
from nagini_contracts.contracts import *


async def main(x: int) -> int:
    Requires(x > 0)
    Ensures(Result() == x)
    return x


#:: ExpectedOutput(call.precondition:assertion.false)
asyncio.run(main(0))
