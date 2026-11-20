"""
Copyright (c) 2026 ETH Zurich
This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.
"""

"""Check that tasks created in an async function are awaited on every path."""


import ast

from nagini_contracts.contracts import CONTRACT_FUNCS, CONTRACT_WRAPPER_FUNCS
from nagini_contracts.obligations import OBLIGATION_CONTRACT_FUNCS
from typing import Dict, FrozenSet, List, Optional, Tuple

from nagini_translation.lib.program_nodes import PythonModule
from nagini_translation.lib.resolver import get_asyncio_function
from nagini_translation.lib.util import get_func_name, InvalidProgramException


State = Optional[FrozenSet[str]]

_CONTRACT_FUNCS = set(CONTRACT_FUNCS + CONTRACT_WRAPPER_FUNCS +
                      OBLIGATION_CONTRACT_FUNCS + ['ThreadPost'])

_ERROR_ID = 'asyncio.task.not.awaited'


def _join(*states: State) -> State:
    reachable = [state for state in states if state is not None]
    if not reachable:
        return None
    return frozenset().union(*reachable)


class PendingTaskChecker:
    """
    Checks that every task an async function creates with ``asyncio.create_task``
    is awaited or handed on (returned, passed to a function or stored) on every
    path through the function, since Nagini does not model the cancellation of
    tasks that are still pending when the event loop finishes.

    The check tracks the local variables that may hold a pending task. A task is
    pending from its creation until a statement awaits or hands on the variable,
    and must not be pending when the function returns, raises an exception or
    ends, or when the variable is overwritten. Exceptions that are not raised
    explicitly are not considered.
    """

    def __init__(self, func: ast.AsyncFunctionDef, module: PythonModule) -> None:
        self._func = func
        self._module = module
        self._parents = {}
        for parent in ast.walk(func):
            for child in ast.iter_child_nodes(parent):
                self._parents[child] = parent
        self._created: Dict[str, ast.Call] = {}
        self._loops: List[Tuple[List[State], List[State]]] = []
        self._raised: List[List[State]] = []

    def check(self) -> None:
        for call in ast.walk(self._func):
            if (self._is_create_task(call) and
                    isinstance(self._parents[call], ast.Expr)):
                raise InvalidProgramException(call, _ERROR_ID,
                                              'Tasks created with asyncio.create_task '
                                              'must be awaited.')
        state = self._block(self._func.body, frozenset())
        self._require_awaited(state, 'the end of the function')

    def _is_create_task(self, node: ast.AST) -> bool:
        return get_asyncio_function(node, self._module) == 'create_task'

    def _require_awaited(self, state: State, location: str) -> None:
        if state:
            name = sorted(state)[0]
            raise InvalidProgramException(
                self._created[name], _ERROR_ID,
                'Task {} might not be awaited before {}.'.format(name, location))

    def _block(self, stmts: List[ast.stmt], state: State) -> State:
        for stmt in stmts:
            if state is None:
                break
            state = self._stmt(stmt, state)
        return state

    def _stmt(self, stmt: ast.stmt, state: State) -> State:
        method = getattr(self, '_stmt_' + stmt.__class__.__name__, None)
        if method is not None:
            return method(stmt, state)
        return self._overwrite(stmt, self._consume(stmt, state))

    def _stmt_Assign(self, stmt: ast.Assign, state: State) -> State:
        state = self._overwrite(stmt, self._consume(stmt.value, state))
        return self._create(stmt.targets[0] if len(stmt.targets) == 1 else None,
                            stmt.value, state)

    def _stmt_AnnAssign(self, stmt: ast.AnnAssign, state: State) -> State:
        if stmt.value is None:
            return state
        state = self._overwrite(stmt, self._consume(stmt.value, state))
        return self._create(stmt.target, stmt.value, state)

    def _stmt_Return(self, stmt: ast.Return, state: State) -> State:
        if stmt.value is not None:
            state = self._consume(stmt.value, state)
        self._require_awaited(state, 'the return in line {}'.format(stmt.lineno))
        return None

    def _stmt_Raise(self, stmt: ast.Raise, state: State) -> State:
        state = self._consume(stmt, state)
        if self._raised:
            self._raised[-1].append(state)
        else:
            self._require_awaited(state, 'the raise in line {}'.format(stmt.lineno))
        return None

    def _stmt_Break(self, stmt: ast.Break, state: State) -> State:
        self._loops[-1][0].append(state)
        return None

    def _stmt_Continue(self, stmt: ast.Continue, state: State) -> State:
        self._loops[-1][1].append(state)
        return None

    def _stmt_If(self, stmt: ast.If, state: State) -> State:
        state = self._consume(stmt.test, state)
        return _join(self._block(stmt.body, state), self._block(stmt.orelse, state))

    def _stmt_While(self, stmt: ast.While, state: State) -> State:
        infinite = isinstance(stmt.test, ast.Constant) and bool(stmt.test.value)
        return self._loop(stmt, state, stmt.test, infinite)

    def _stmt_For(self, stmt: ast.For, state: State) -> State:
        state = self._consume(stmt.iter, state)
        return self._loop(stmt, state, None, False)

    def _loop(self, stmt: ast.stmt, state: State, test: Optional[ast.expr],
              infinite: bool) -> State:
        entry = state
        while True:
            head = self._consume(test, entry) if test is not None else entry
            if isinstance(stmt, ast.For):
                head = self._overwrite(stmt.target, head)
            breaks, continues = [], []
            self._loops.append((breaks, continues))
            end = self._block(stmt.body, head)
            self._loops.pop()
            new_entry = _join(state, end, *continues)
            if new_entry == entry:
                break
            entry = new_entry
        exit_state = None if infinite else self._block(stmt.orelse, head)
        return _join(exit_state, *breaks)

    def _stmt_Try(self, stmt: ast.Try, state: State) -> State:
        self._raised.append([])
        body_end = self._block(stmt.body, state)
        raised = self._raised.pop()
        created = frozenset(name for name in self._created_in(stmt.body))
        handler_entry = _join(state, body_end, *raised)
        if handler_entry is not None:
            handler_entry = handler_entry | created
        ends = [self._block(stmt.orelse, body_end)]
        for handler in stmt.handlers:
            ends.append(self._block(handler.body, handler_entry))
        if not stmt.handlers:
            for raised_state in raised:
                self._require_awaited(raised_state, 'an exception is raised')
        end = _join(*ends)
        if stmt.finalbody and end is not None:
            end = self._block(stmt.finalbody, end)
        return end

    def _stmt_TryStar(self, stmt: ast.AST, state: State) -> State:
        return self._stmt_Try(stmt, state)

    def _stmt_Match(self, stmt: ast.Match, state: State) -> State:
        state = self._consume(stmt.subject, state)
        ends = [state]
        for case in stmt.cases:
            case_state = state
            if case.guard is not None:
                case_state = self._consume(case.guard, case_state)
            ends.append(self._block(case.body, case_state))
        return _join(*ends)

    def _stmt_With(self, stmt: ast.With, state: State) -> State:
        for item in stmt.items:
            state = self._consume(item.context_expr, state)
        return self._block(stmt.body, state)

    def _created_in(self, stmts: List[ast.stmt]) -> List[str]:
        names = []
        for stmt in stmts:
            for node in ast.walk(stmt):
                if isinstance(node, (ast.Assign, ast.AnnAssign)):
                    targets = node.targets if isinstance(node, ast.Assign) else [node.target]
                    if (len(targets) == 1 and isinstance(targets[0], ast.Name) and
                            self._is_create_task(node.value)):
                        names.append(targets[0].id)
        return names

    def _create(self, target: Optional[ast.expr], value: ast.expr,
                state: State) -> State:
        if not (self._is_create_task(value) and isinstance(target, ast.Name)):
            return state
        self._created[target.id] = value
        return state | {target.id}

    def _overwrite(self, node: ast.AST, state: State) -> State:
        for name in ast.walk(node):
            if (isinstance(name, ast.Name) and isinstance(name.ctx, ast.Store) and
                    name.id in state):
                line = getattr(name, 'lineno', None)
                self._require_awaited(frozenset([name.id]),
                                      'it is overwritten in line {}'.format(line))
        return state

    def _consume(self, node: ast.AST, state: State) -> State:
        handed_on = {use.id for use in ast.walk(node)
                     if isinstance(use, ast.Name) and isinstance(use.ctx, ast.Load) and
                     use.id in state and self._is_handed_on(use)}
        return state - handed_on

    def _is_handed_on(self, use: ast.Name) -> bool:
        parent = self._parents[use]
        if isinstance(parent, ast.keyword):
            parent = self._parents[parent]
        if isinstance(parent, ast.Call):
            return use is not parent.func and get_func_name(parent) not in _CONTRACT_FUNCS
        return isinstance(parent, (ast.Await, ast.Return, ast.Assign, ast.AnnAssign,
                                   ast.Tuple, ast.List, ast.Set, ast.Dict))
