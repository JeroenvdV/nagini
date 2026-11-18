# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from typing import AsyncIterator
from nagini_contracts.contracts import *


#:: ExpectedOutput(unsupported:async generators)
async def numbers() -> AsyncIterator[int]:
    yield 1
