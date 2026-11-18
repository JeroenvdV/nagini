# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *


def main(x: int) -> int:
    Requires(x > 0)
    Ensures(Result() == x)
    return x


y = main(3)
assert y == 3
#:: ExpectedOutput(assert.failed:assertion.false)
assert False
