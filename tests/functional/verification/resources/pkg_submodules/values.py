# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *

K = 4


@Pure
def double(x: int) -> int:
    return 2 * x


class Box:
    def __init__(self, v: int) -> None:
        self.v = v
        Ensures(Acc(self.v) and self.v == v)
