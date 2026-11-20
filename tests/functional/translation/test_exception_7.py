# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *


def f(i: int) -> int:
    #:: ExpectedOutput(unsupported:Exsures only supports Exception and user-defined exception classes but got ValueError.)
    Exsures(ValueError, True)
    return i
