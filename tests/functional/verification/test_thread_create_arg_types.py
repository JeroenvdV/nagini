# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from nagini_contracts.contracts import *
from nagini_contracts.thread import Thread
from nagini_contracts.obligations import MustTerminate


class Cell:
    def __init__(self) -> None:
        self.val = 0
        Ensures(Acc(self.val) and self.val == 0)


def decr(c: Cell, n: int) -> int:
    Requires(Acc(c.val))
    Requires(MustTerminate(2))
    Ensures(Acc(c.val) and c.val == Old(c.val) - n)
    c.val = c.val - n
    return c.val


def client_create_correct_args() -> Thread:
    cl = Cell()
    t = Thread(None, decr, args=(cl, 6))
    return t


def client_create_first_arg_wrong() -> Thread:
    #:: ExpectedOutput(thread.creation.failed:invalid.argument.type)
    t = Thread(None, decr, args=(6, 6))
    return t


def client_create_two_wrong_args() -> Thread:
    cl = Cell()
    #:: ExpectedOutput(thread.creation.failed:invalid.argument.type)
    t = Thread(None, decr, args=(6, cl))
    return t
