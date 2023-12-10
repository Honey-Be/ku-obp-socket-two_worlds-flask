from typing import Callable, Self, List, Type, TypeVar, Generic, ParamSpec, ParamSpecArgs, ParamSpecKwargs
from cells import AbstractCellData

import copy

class DictMerger:
    def __init__(self, internal: dict[int,AbstractCellData] = {}):
        self._internal: dict[int,AbstractCellData] = internal
    def merge[C: AbstractCellData](self, d: dict[int,C]) -> Self:
        new_internal = copy.copy(self._internal)
        dkeys = filter(lambda key: key not in self._internal.keys(),d.keys())
        for key in dkeys:
            new_internal[key] = d[key]
        return DictMerger(new_internal)
    def extract(self):
        return copy.deepcopy(self._internal)