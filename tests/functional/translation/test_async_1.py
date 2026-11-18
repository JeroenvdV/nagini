# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *


async def f() -> int:
    return 1


async def g() -> int:
    #:: ExpectedOutput(unsupported:Coroutine objects are not supported; calls of async functions must be awaited directly.)
    c = f()
    return 2
