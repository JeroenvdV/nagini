# Any copyright is dedicated to the Public Domain.
# http://creativecommons.org/publicdomain/zero/1.0/

from typing import Dict, List, Optional, Set, Tuple as Pair
from nagini_contracts.contracts import *


@Predicate
def valid(d: Dict[int, int]) -> bool:
    return Acc(dict_pred(d))


@Pure
def first(p: Pair[int, int]) -> int:
    return p[0]


def total(l: List[int], o: Optional[int]) -> int:
    Requires(Acc(list_pred(l)))
    Ensures(Acc(list_pred(l)))
    Ensures(Result() == len(l))
    return len(l)


def size(p: 'Pair[int, int]') -> int:
    Requires(first(p) > 0)
    return p[1]
