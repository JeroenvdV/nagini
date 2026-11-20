# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *
from nagini_contracts.thread import Thread


async def f() -> None:
    pass


def g() -> None:
    #:: ExpectedOutput(invalid.program:invalid.thread.creation)
    t = Thread(target=f, args=())
