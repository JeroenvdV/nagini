# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *
from resources.pkg_submodules import values, shadowed
from resources.pkg_submodules import values as v2, vals


Assert(values.K == 4)


def use_submodule() -> None:
    b = values.Box(3)
    Assert(b.v == 3)
    Assert(v2.double(values.K) == 8)
    Assert(vals.K == v2.K)
    #:: ExpectedOutput(assert.failed:assertion.false)
    Assert(values.K == 5)


def use_shadowing_name() -> int:
    Ensures(Result() == 4)
    return shadowed + 1
