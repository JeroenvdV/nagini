# async/await support: design notes

This document describes how Nagini encodes `async def`, `await` and the
supported parts of `asyncio`. See [async.md](async.md) for the user
documentation.

## Encoding

Each construct is encoded with a mechanism Nagini already has: methods and
calls for coroutines, and the thread fork/join encoding for tasks.

| Python | Nagini encoding |
|---|---|
| `async def f(...)` | ordinary impure method with the same contract (`Requires`/`Ensures`/`Exsures`/`MustTerminate`) |
| `await f(args)` | method call of `f` |
| `asyncio.run(f(args))` | method call of `f`, only in module-level code |
| `await asyncio.sleep(d)` | evaluates `d`; a suspension point |
| `asyncio.create_task(f(args))` | `Thread(target=f, args=...)` + `start`, without `MayStart` |
| `await t`, `t: asyncio.Task[T]` | `t.join(...)` over all possible async targets, plus the coroutine's result |
| `await asyncio.gather(f(a), g(b))` | `create_task` for each coroutine in order, then awaiting each task with its known target; the result is the tuple of results |
| `asyncio.Task[T]` | builtin class `Task[T]` extending `Thread` |

- mypy gives an `async def` declared to return `T` the type
  `Coroutine[Any, Any, T]`; `lib/typeinfo.py` unwraps it to `T`.
- A flag on the context (`Context.awaited_call`) marks the call that is being
  awaited. Any other call of an async function is rejected.
- `asyncio` is in `IGNORED_IMPORTS`. The names a module imports from `asyncio`
  are recorded in `PythonModule.asyncio_aliases`, and
  `resolver.get_asyncio_function` uses them to recognise `asyncio` calls.

Soundness argument: tasks of one event loop only interleave at `await` points.
Nagini's permission system already rules out interference from preemptive
threads, so it also rules out interference from cooperatively scheduled tasks.
Anything the awaiting code keeps (does not pass to the callee or task) cannot be
changed while it is suspended.

`gather` wraps every coroutine in a task and waits for all of them, so it is
encoded exactly like that. All preconditions are exhaled before any
postcondition is inhaled, so the coroutines must be able to run at the same
time. Since the target of each task is known, the await inhales only that
target's postcondition, and the size of the encoding does not depend on the
number of async methods in the program.

Additional checks specific to asyncio:

- **Locks held across `await`.** At every `await`, Nagini asserts that the
  current method holds no `MustRelease` obligation. Otherwise another task
  blocking on that lock would block the event loop thread forever, which is a
  deadlock the thread model would not catch.
- **`asyncio.run` placement.** Only allowed at module level, because calling it
  inside a running loop raises `RuntimeError`.
- **`create_task` placement.** Only allowed in `async def`, because it needs a
  running loop.
- **Task targets.** Task coroutines (including the arguments of `gather`) must
  not declare exceptions (they would be re-raised by `await t`), must not be
  class methods, must not have keyword or default arguments, and must not
  mention `WaitLevel()` in their postconditions.
- **Coroutine objects.** Storing a coroutine without awaiting it directly is
  rejected, as are async thread targets, sync/async overrides, and
  `@Pure`/`@Predicate`/`@Inline`/`@Ghost`/`@property` on `async def`.

## Limitations

### Soundness and assumptions

- **Cancellation is not modelled.** Tasks still pending when the main coroutine
  returns get `CancelledError` at their `await` points. Code that only runs on
  that path, such as `finally` blocks or error handlers, is not verified, and
  nothing enforces that every task is awaited: a task that is never awaited
  verifies without a warning.
- **Termination assumes fair cooperative scheduling.** A task that loops
  without awaiting starves the others. `sleep` and awaits of coroutines assume
  that the event loop eventually resumes the current task.
- **The lock check only covers Nagini's `Lock`** (its `MustRelease`
  obligations). Blocking calls inside a task, such as `Thread.join` or blocking
  I/O, are not flagged even though they block the event loop.
- **Typing of awaited results relies on mypy.** The result of `await t` is
  assumed to have type `T` from `Task[T]`.
- **Other `asyncio` types** in annotations (for example `asyncio.Queue[int]`)
  are converted to a placeholder class. Calls on them are rejected as
  unsupported.

### Expressiveness

- Not supported: `asyncio.wait`, `ensure_future`, `TaskGroup`,
  `asyncio.Lock`/`Event`/`Queue`, `Task.cancel`, `async for`, `async with`,
  async generators, and coroutine objects stored in variables, passed around or
  awaited later.
- `gather` only accepts direct calls of async functions (not tasks or other
  awaitables) and no keyword arguments such as `return_exceptions`.
- `create_task` is only allowed inside `async def`; `asyncio.run` only at module
  level with a single coroutine argument; `asyncio.sleep` only with a single
  argument.
- Awaiting a task of unknown origin considers every eligible async method in
  the program as its possible target, so the Viper code grows with the program
  size times the number of task awaits.
- Awaiting the same task twice returns the same result (the result is
  `getResult(t)`, a function of the task), but the second await does not
  obtain the postcondition again.

### Testing gaps

- Carbon has not been run on the async tests.
- Information-flow mode (`--sif`): coroutines work, but tasks and `gather` are
  rejected there, like threads.
- Not tested together with I/O contracts or with `--functional-product`.
- `await` inside contracts, lambdas or comprehensions, `await` in ghost code,
  and awaiting calls on receivers of union type are untested.

## Changed files

- `lib/typeinfo.py`: unwrap mypy's `Coroutine[Any, Any, T]` return type of
  `async def` to `T`.
- `analyzer.py`: `AsyncFunctionDef` handling, restrictions, `asyncio` import
  aliases, mapping of `asyncio.Task` to the builtin `Task` class, rejection of
  coroutine-typed values.
- `translators/call.py`: `translate_Await`, `asyncio.run`/`sleep`/
  `create_task`/`gather`, task await; thread object creation is shared between
  threads and tasks.
- `translators/obligation/interface.py`: `create_no_must_release_check`.
- `lib/resolver.py`: types of `await` expressions, `asyncio.run(...)`,
  `create_task(...)` and `gather(...)`.
- `resources/builtins.json`: `Task` class.
- `nagini_contracts/thread.py` and `obligations.py`: thread contract functions
  and `Level` accept `asyncio.Task`.
- `models/converter.py`: counterexamples for tuples with `None` elements.
- `ghost/ghost_checker.py`: `raise` statements in `@ContractOnly` bodies are
  kept by `--extraction`; `X | Y` annotations are supported.
- `translators/program.py`: module-level code is verified when the program
  defines a function named `main`.
- `translators/expression.py`: calls of functions returning `None` can be used
  as expressions, e.g. `return f()`.
- Small `FunctionDef` → `FunctionDef | AsyncFunctionDef` generalisations in the
  ghost checker, extraction, statement translator, error messages and utilities.
- Tests: `tests/functional/verification/test_async*.py`,
  `tests/functional/translation/test_async_*.py`,
  `tests/functional/extraction/test_async.py`.
