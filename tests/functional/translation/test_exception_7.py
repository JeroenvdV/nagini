# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *


def f(i: int) -> int:
    #:: ExpectedOutput(unsupported:Unsupported exception type.)
    Exsures(ValueError, True)
    return i
