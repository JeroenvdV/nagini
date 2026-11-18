# Async/await

Nagini can verify `async def` functions and methods, `await`, and the core of
`asyncio` (`run`, `sleep`, `create_task`, `gather`). Every construct is encoded with a
feature Nagini already has:

| Python | Encoded like |
|---|---|
| `async def f(...)` | an ordinary (impure) method with the same contract |
| `await f(args)` | a call of `f`: its precondition is exhaled, its postcondition inhaled |
| `asyncio.run(f(args))` | a call of `f`; only allowed in module-level code |
| `await asyncio.sleep(d)` | evaluating `d` (a pure suspension point) |
| `t = asyncio.create_task(f(args))` | creating and immediately starting a thread with target `f` |
| `await t` (with `t: asyncio.Task[T]`) | joining that thread, additionally returning the result of `f` |
| `await asyncio.gather(f(a), g(b))` | starting a thread for each coroutine, then joining each of them; returns the tuple of results |

```python
import asyncio
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


class Cell:
    def __init__(self) -> None:
        Requires(MustTerminate(1))
        self.val = 0
        Ensures(Acc(self.val) and self.val == 0)


async def work(c: Cell, n: int) -> int:
    Requires(Acc(c.val))
    Requires(MustTerminate(2))
    Ensures(Acc(c.val) and c.val == Old(c.val) + n)
    Ensures(Result() == n * 2)
    await asyncio.sleep(0)
    c.val = c.val + n
    return n * 2


async def main() -> int:
    Ensures(Result() == 14)
    a = Cell()
    b = Cell()
    t1 = asyncio.create_task(work(a, 3))   # t1 now owns Acc(a.val)
    t2 = asyncio.create_task(work(b, 4))
    r1 = await t1                          # Acc(a.val) and a.val == 3 come back
    r2 = await t2
    assert a.val == 3 and b.val == 4
    return r1 + r2


asyncio.run(main())
```

## Why this is sound

All tasks of an event loop run on one thread and only switch at `await`
points. Nagini's permissions already rule out interference from arbitrary
(preemptive) threads, so they also rule out interference from other tasks: a
task can only read or write locations it holds a permission to, and whatever
the awaiting code does not pass to the callee or task stays with it while it is
suspended. Cooperative scheduling is a special case of the thread model.

## Coroutines

* Contracts of `async def` functions use the usual `Requires`, `Ensures`,
  `Exsures`, `Result()` and `Old()`; they describe the execution of the
  coroutine body, i.e., what happens when the coroutine is awaited.
* Calls of async functions must be awaited directly (`await f(x)`, also nested
  as in `await f(await g())`). Storing a coroutine object (`c = f(x)`) is
  reported as unsupported.
* `async def` cannot be combined with `@Pure`, `@Predicate`, `@Inline`,
  `@IOOperation`, `@property`, `@Ghost` or `@Opaque`, cannot be `__init__` or
  another magic method, and async and non-async methods cannot override each
  other.
* Termination is proved as usual with `Requires(MustTerminate(n))`; awaiting a
  coroutine counts as a call.
* `asyncio.run(f(...))` must be used in module-level statements (for example in
  `if __name__ == '__main__':`). Inside a function it might run while an event
  loop is already running, which raises a `RuntimeError`.

## Tasks

`asyncio.create_task(f(args))` may only be used in async functions. Creating
the task exhales the precondition of `f`; if `f` promises to terminate
(`MustTerminate`), the creator gets `Joinable(t)` and a full permission to
`ThreadPost(t)`. The contract functions from `nagini_contracts.thread`
(`getMethod`, `getArg`, `getOld`, `arg`, `Joinable`, `ThreadPost`) and `Level`
from `nagini_contracts.obligations` accept tasks, so tasks can be passed
between functions:

```python
from asyncio import Task, create_task
from nagini_contracts.thread import ThreadPost, Joinable, getArg, getMethod, getOld, arg
from nagini_contracts.obligations import WaitLevel, Level


async def finish(t: Task[int], c: Cell) -> int:
    Requires(Acc(ThreadPost(t)))
    Requires(getMethod(t) == work)
    Requires(getArg(t, 0) is c and getArg(t, 1) == 5)
    Requires(getOld(t, arg(0).val) == 10)
    Requires(WaitLevel() < Level(t))
    Ensures(Acc(c.val) and c.val == 15)
    Ensures(Result() == 10)
    return await t
```

Awaiting a task requires `Joinable(t)` (the task terminates) and
`WaitLevel() < Level(t)`, exactly like `Thread.join`. If some permission to
`ThreadPost(t)` is held, that fraction of the coroutine's postcondition is
obtained and the permission is consumed. Awaiting the same task again returns
the same result, but its postcondition is not obtained again. Task coroutines must not be class methods,
must not declare exceptions (an exception in a task is re-raised when it is
awaited), and their postconditions must not mention `WaitLevel()`.

## Gathering coroutines

`await asyncio.gather(f(a), g(b), ...)` runs the given coroutines concurrently
and waits until all of them have finished. It is encoded like creating a task
for each coroutine, in order, and then awaiting each of these tasks. Since the
coroutine of each task is known, only its own postcondition is obtained. The
result is a tuple with the coroutines' results, which can be unpacked:

```python
async def read(c: Cell) -> int:
    Requires(Acc(c.val, 1/4))
    Requires(MustTerminate(2))
    Ensures(Acc(c.val, 1/4) and Result() == c.val)
    return c.val


async def both(a: Cell, b: Cell) -> int:
    Requires(Acc(a.val) and Acc(b.val) and a.val == 5)
    Ensures(Acc(a.val) and Acc(b.val) and b.val == Old(b.val) + 1)
    Ensures(Result() == 12)
    r1, r2, r3 = await asyncio.gather(read(a), read(a), work(b, 1))
    return r1 + r2 + r3
```

* Since all coroutines run at the same time, the preconditions of all of them
  must hold together: the permissions they require are split between them, and
  a location that one coroutine writes cannot be accessed by another one.
* Every coroutine must promise to terminate (`MustTerminate`), and its level
  must be above the current wait level, as for awaiting a task.
* The arguments of `gather` must be direct calls of async functions or methods
  and are subject to the same restrictions as task coroutines. Tasks and other
  awaitables as arguments, keyword arguments such as `return_exceptions`, and
  `gather` without arguments are reported as unsupported, as is using `gather`
  without awaiting it directly.
* Results of coroutines that return `None` are `None` in the tuple. Tuples of
  more than nine elements are not supported.

## Locks

A task must not hold a lock (a `MustRelease` obligation) at an `await`: another
task that tries to acquire the lock would block the whole event loop thread, so
the lock could never be released. Nagini checks this at every `await` and
reports `Await may fail. A lock might be held while suspending the current
task.`

## Interfaces

`@ContractOnly` async functions and methods can be used as interfaces that are
implemented in unverified code. Their body is not verified, and `--extraction`
removes everything except `raise` statements, so a body such as
`raise NotImplementedError()` is kept in the extracted program.

## Not supported

`async for`, `async with`, async generators, `asyncio.wait`, `TaskGroup`,
`asyncio.Lock`/`Queue`/`Event`, `ensure_future`, task cancellation, and any
other `asyncio` function are reported as unsupported.

Tasks that are still pending when the coroutine passed to `asyncio.run`
returns are cancelled by asyncio. Nagini does not model cancellation
(`CancelledError` raised at an `await`), so code that only runs on that path,
such as `finally` blocks in a cancelled task, is not verified. Await every task
you create to stay within the verified model.

