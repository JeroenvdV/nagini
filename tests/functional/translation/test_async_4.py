# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *


@Pure
#:: ExpectedOutput(invalid.program:async.decorator.unsupported)
async def f() -> int:
    return 1
