# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

import asyncio
from nagini_contracts.contracts import *
from nagini_contracts.lock import Lock
from nagini_contracts.obligations import MustTerminate, WaitLevel, Level


class Counter:
    def __init__(self) -> None:
        Requires(MustTerminate(1))
        self.value = 0
        Ensures(Acc(self.value) and self.value == 0)

    async def add(self, n: int) -> int:
        Requires(Acc(self.value))
        Ensures(Acc(self.value) and self.value == Old(self.value) + n)
        Ensures(Result() == self.value)
        await asyncio.sleep(0)
        self.value += n
        return self.value


class CounterLock(Lock[Counter]):
    @Predicate
    def invariant(self) -> bool:
        return Acc(self.get_locked().value)


class NegativeError(Exception):
    pass


async def inc(x: int) -> int:
    Requires(MustTerminate(1))
    Ensures(Result() == x + 1)
    return x + 1


async def twice(x: int) -> int:
    Ensures(Result() == x + 2)
    y = await inc(x)
    return await inc(y)


async def positive(x: int) -> int:
    Requires(MustTerminate(1))
    Ensures(x >= 0 and Result() == x)
    Exsures(NegativeError, x < 0)
    if x < 0:
        raise NegativeError()
    return x


async def nested_awaits() -> None:
    c = Counter()
    r = await c.add(3)
    assert r == 3
    await c.add(await twice(1))
    assert c.value == 6
    await asyncio.sleep(1)
    assert c.value == 6
    #:: ExpectedOutput(assert.failed:assertion.false)
    assert c.value == 7


async def wrong_result(x: int) -> int:
    #:: ExpectedOutput(postcondition.violated:assertion.false)
    Ensures(Result() == x)
    return await inc(x)


async def missing_permission(c: Counter) -> None:
    #:: ExpectedOutput(call.precondition:insufficient.permission)
    await c.add(1)


async def frame(c: Counter, d: Counter) -> None:
    Requires(Acc(c.value) and Acc(d.value) and d.value == 5)
    Ensures(Acc(c.value) and Acc(d.value) and d.value == 5)
    await c.add(2)


async def exceptions(x: int) -> int:
    Ensures(Result() >= 0)
    try:
        return await positive(x)
    except NegativeError:
        return 0


#:: ExpectedOutput(exhale.failed:assertion.false)
async def undeclared_exception() -> int:
    return await positive(-1)


async def terminating(c: Counter) -> int:
    Requires(MustTerminate(2))
    Ensures(Result() == 3)
    return await inc(2)


async def non_terminating_callee() -> None:
    Requires(MustTerminate(2))
    #:: ExpectedOutput(leak_check.failed:caller.has_unsatisfied_obligations)
    await twice(2)


async def lock_held_while_suspended(l: CounterLock) -> None:
    Requires(WaitLevel() < Level(l))
    l.acquire()
    #:: ExpectedOutput(await.failed:lock.held)
    await asyncio.sleep(0)
    l.release()


async def lock_held_while_awaiting(l: CounterLock) -> None:
    Requires(WaitLevel() < Level(l))
    l.acquire()
    #:: ExpectedOutput(await.failed:lock.held)
    await inc(2)
    l.release()


async def lock_released_before_await(l: CounterLock) -> None:
    Requires(WaitLevel() < Level(l))
    l.acquire()
    l.release()
    await asyncio.sleep(0)


async def main() -> int:
    Ensures(Result() == 4)
    await nested_awaits()
    return await twice(2)


result = asyncio.run(main())
assert result == 4
