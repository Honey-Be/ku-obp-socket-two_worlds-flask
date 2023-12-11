from enum import Enum
from abc import ABC, ABCMeta, abstractproperty, abstractmethod
from typing import Any, Self
from manager import AbstractPaymentType, GameStateType, PlayerIconType

from primitives import *
from primitives import AbstractPaymentType, GameStateType, PlayerIconType

from manager import *

from random import choice

from chances import CHANCE_CARDS

class CellType(Enum):
    infrastructure = "infrastructure"
    industrial = "industrial"
    land = "land"
    lotto = "lotto"
    charity = "charity"
    chance = "chance"
    transportation = "transportation"
    hospital = "hospital"
    park = "park"
    concert = "concert"
    university = "university"
    jail = "jail"
    start = "start"

class BuildableFlagType(Enum):
    NotBuildable = 0
    OnlyOne = 1
    Normal = 3

class AbstractCellData(metaclss=ABCMeta):
    def __new__(cls, maxBuildable: BuildableFlagType):
        this: Self = super().__new__(cls)
        cls._maxBuildable: BuildableFlagType = maxBuildable
        return this
    
    def __init__(self, cell_type: CellType, cell_id: int, name: str, group_factor: int = 0):
        self._cell_type: CellType = cell_type
        self._cell_id: int = cell_id
        self._name: str = name
        self.group_factor: int = group_factor
    
    @property
    def cell_type(self) -> CellType:
        return self._cell_type

    @property
    def name(self) -> str:
        return self._name

    @property
    @classmethod
    def maxBuildable(cls) -> BuildableFlagType:
        return cls._maxBuildable

    @property
    @abstractmethod
    def mandatoryPaymentInfos(self) -> Sequence[AbstractPaymentType]: pass
    
    @property
    @abstractmethod
    def optionalPaymentInfos(self) -> Sequence[AbstractPaymentType]: pass

    @property
    def cellId(self) -> int:
        return self._cell_id
    
    @property
    def groupId(self) -> int: return self.group_factor

    @property
    @abstractmethod
    def hasEffectWhenPassing(self) -> bool: pass
    
    @abstractmethod
    def passing(self, state: GameStateType, player_now_icon: PlayerIconType) -> GameStateType: pass

    @abstractmethod
    def arrived(self, state: GameStateType, player_now_icon: PlayerIconType, callback: Callable[[GameStateType], None]) -> tuple[GameStateType, Sequence[AbstractPaymentType]]: pass

class Infrastructure(AbstractCellData):
    def __new__(cls):
        this: Self = super().__new__(cls,BuildableFlagType.NotBuildable)
        cls._payment_infos: Sequence[AbstractPaymentType] = [
            UnidirectionalPayment("P2G",300000)
        ]
        return this

    def __init__(self, kind: str):
        (_cellId, _name) = CellNameLookups.infrastructure(kind)
        super().__init__(CellType.infrastructure,_cellId, _name)

    @property
    @override
    def mandatoryPaymentInfos(self) -> Sequence[AbstractPaymentType]:
        return Infrastructure._payment_infos
    
    @property
    @override
    def optionalPaymentInfos(self) -> Sequence[AbstractPaymentType]:
        return []
    
    @override
    def passing(self, state: GameStateType, player_icon: PlayerIconType) -> GameStateType:
        return state
    
    @property
    @override
    def hasEffectWhenPassing(self) -> bool:
        return False
    
    @override
    def arrived(self, state: GameStateType, player_now_icon: PlayerIconType, callback: Callable[[GameStateType], None]) -> tuple[GameStateType, Sequence[AbstractPaymentType]]:
        transactor = UnidirectionalTransactor(player_now_icon)
        merged_mandatory = mergeTransactions(map(transactor.transact,self.mandatoryPaymentInfos))
        new_state = merged_mandatory.toAppliedState(state)
        callback(new_state)
        return (new_state, [])
class Land(AbstractCellData):
    def __new__(cls, cell_id: int, name: str, group_factor: int):
        this: Self = super().__new__(cls,BuildableFlagType.Normal)
        cls._optional_payment_infos: Sequence[AbstractPaymentType] = [
            P2OPayment(300000)
        ]
        return this

    def __init__(self, cell_id: int, name: str, group_factor: int):
        super().__init__(CellType.land,cell_id,name, group_factor)

    @property
    @override
    def mandatoryPaymentInfos(self) -> Sequence[AbstractPaymentType]:
        return [UnidirectionalPayment("P2G",self.group_factor * 100000)]
    
    @property
    @override
    def optionalPaymentInfos(self) -> Sequence[AbstractPaymentType]:
        return Land._optional_payment_infos
    
    @override
    def passing(self, state: GameStateType, player_icon: PlayerIconType) -> GameStateType:
        return state
        
    @property
    @override
    def hasEffectWhenPassing(self) -> bool:
        return False
    
    @override
    def arrived(self, state: GameStateType, player_now_icon: PlayerIconType, callback: Callable[[GameStateType], None]) -> tuple[GameStateType, Sequence[AbstractPaymentType]]:
        transactor = UnidirectionalTransactor(player_now_icon)
        merged_mandatory = mergeTransactions(map(transactor.transact,self.mandatoryPaymentInfos))
        if self.cellId in state.properties.keys():
            p2o_transactor = P2OTransactor(player_now_icon,state.properties[self.cellId].ownerIcon)
            merged_p2o = mergeTransactions(map(p2o_transactor.transact,self.optionalPaymentInfos))

            group_cellIds = _getGroupCellIds(self.cellId)
            filtered = filter(lambda cid: cid in state.properties.keys(),group_cellIds)
            group_owned_counts = list(map(lambda cid: state.properties[cid].count,filtered))

            if len(group_owned_counts) == len(group_cellIds):
                c = min(group_owned_counts) + 1
                new_state = (merged_mandatory + merged_p2o * c).toAppliedState(state)
            else:
                new_state = (merged_mandatory + merged_p2o).toAppliedState(state)
            callback(new_state)
            if state.properties[self.cellId].ownerIcon == player_now_icon and state.properties[self.cellId].count < 3:
                return (new_state, self.optionalPaymentInfos)
            else:
                return (new_state, [])
        else:
            new_state = merged_mandatory.toAppliedState(state)
            callback(new_state)
            return (new_state, self.optionalPaymentInfos)

class Lotto(AbstractCellData):
    def __new__(cls):
        this: Self = super().__new__(cls, BuildableFlagType.NotBuildable)
        cls._payment_infos: Sequence[AbstractPaymentType] = [
            UnidirectionalPayment("P2M",200000)
        ]
        return this
    def __init__(self, cell_id: int = 3):
        super().__init__(CellType.lotto,cell_id,"로또")

    @property
    @override
    def mandatoryPaymentInfos(self) -> Sequence[AbstractPaymentType]:
        return []
    
    @property
    @override
    def optionalPaymentInfos(self) -> Sequence[AbstractPaymentType]:
        return Lotto._payment_infos
    
    @override
    def passing(self, state: GameStateType, player_icon: PlayerIconType) -> GameStateType:
        return state
    
    @property
    @override
    def hasEffectWhenPassing(self) -> bool:
        return False
    
    @override
    def arrived(self, state: GameStateType, player_now_icon: PlayerIconType, callback: Callable[[GameStateType], None]) -> tuple[GameStateType, Sequence[AbstractPaymentType]]:
        return (state, self.optionalPaymentInfos)

class Charity(AbstractCellData):
    def __new__(cls):
        this: Self = super().__new__(cls, BuildableFlagType.NotBuildable)
        cls._payment_infos: Sequence[AbstractPaymentType] = [
            UnidirectionalPayment("P2C",600000)
        ]
        return this
    def __init__(self, cell_id: int = 52):
        super().__init__(CellType.charity,cell_id,"구제기금")
    
    @property
    @override
    def mandatoryPaymentInfos(self) -> Sequence[AbstractPaymentType]:
        return Charity._payment_infos
    
    @property
    @override
    def optionalPaymentInfos(self) -> Sequence[AbstractPaymentType]:
        return []
    
    @override
    def passing(self, state: GameStateType, player_icon: PlayerIconType) -> GameStateType:
        return state
    
    @property
    @override
    def hasEffectWhenPassing(self) -> bool:
        return False

    @override
    def arrived(self, state: GameStateType, player_now_icon: PlayerIconType, callback: Callable[[GameStateType], None]) -> tuple[GameStateType, Sequence[AbstractPaymentType]]:
        transactor = UnidirectionalTransactor(player_now_icon)
        merged_mandatory = mergeTransactions(map(transactor.transact,self.mandatoryPaymentInfos))
        new_state = merged_mandatory.toAppliedState(state)
        
        callback(new_state)
        return (new_state, [])
class Chance(AbstractCellData):
    def __new__(cls, cell_id: int):
        this: Self = super().__new__(cls, BuildableFlagType.NotBuildable)
        return this
    def __init__(self, cell_id: int):
        super().__init__(CellType.chance,cell_id,"변화카드")

    @property
    @override
    def mandatoryPaymentInfos(self) -> Sequence[AbstractPaymentType]:
        return []
    @property
    @override
    def optionalPaymentInfos(self) -> Sequence[AbstractPaymentType]:
        return []
    
    @override
    def passing(self, state: GameStateType, player_icon: PlayerIconType) -> GameStateType:
        return state
    
    @property
    @override
    def hasEffectWhenPassing(self) -> bool:
        return False
    
    @override
    def arrived(self, state: GameStateType, player_now_icon: PlayerIconType, callback: Callable[[GameStateType], None]) -> tuple[GameStateType, Sequence[AbstractPaymentType]]:
        picked = choice(CHANCE_CARDS)
        fmed = set(map(lambda player: player.icon, filter(lambda player: (player.icon == player_now_icon),state.players)))
        new_state = reduce(lambda acc,curr: picked.action(copy.deepcopy(acc), curr),fmed,state)
        callback(new_state)
        return (new_state, [])
    

class Trnsportation(AbstractCellData):
    def __new__(cls, cell_id: int, dest: int):
        this: Self = super().__new__(cls, BuildableFlagType.NotBuildable)
        return this
    def __init__(self, cell_id: int, dest: int):
        super().__init__(CellType.transportation,cell_id,"대중교통")
        self._dest: int = dest

    @property
    @override
    def mandatoryPaymentInfos(self) -> Sequence[AbstractPaymentType]:
        return []
    @property
    @override
    def optionalPaymentInfos(self) -> Sequence[AbstractPaymentType]:
        return []
    
    @override
    def passing(self, state: GameStateType, player_icon: PlayerIconType) -> GameStateType:
        return state
    
    @property
    def dest(self) -> int:
        return self._dest
    
    @property
    @override
    def hasEffectWhenPassing(self) -> bool:
        return False
    
    @override
    def arrived(self, state: GameStateType, player_now_icon: PlayerIconType, callback: Callable[[GameStateType], None]) -> tuple[GameStateType, Sequence[AbstractPaymentType]]:
        return warp(state,player_now_icon,self.dest,callback,do_arrived=False)

class Hospital(AbstractCellData):
    def __new__(cls):
        this: Self = super().__new__(cls, BuildableFlagType.NotBuildable)
        cls._payment_infos: Sequence[AbstractPaymentType] = [
            UnidirectionalPayment("P2M",200000)
        ]
        return this
    def __init__(self, cell_id: int = 45):
        super().__init__(CellType.hospital,cell_id,"병원")

    @property
    @override
    def mandatoryPaymentInfos(self) -> Sequence[AbstractPaymentType]:
        return Hospital._payment_infos
    
    @property
    @override
    def optionalPaymentInfos(self) -> Sequence[AbstractPaymentType]:
        return []
    
    @override
    def passing(self, state: GameStateType, player_icon: PlayerIconType) -> GameStateType:
        return state
    
    @override
    def arrived(self, state: GameStateType, player_now_icon: PlayerIconType, callback: Callable[[GameStateType], None]) -> tuple[GameStateType, Sequence[AbstractPaymentType]]:
        transactor = UnidirectionalTransactor(player_now_icon)
        merged = mergeTransactions(map(transactor.transact,self.mandatoryPaymentInfos))
        new_state = merged.toAppliedState(state)
        
        callback(new_state)
        return (new_state, [])
    
    @property
    @override
    def hasEffectWhenPassing(self) -> bool:
        return False

class Park(AbstractCellData):
    def __new__(cls):
        this: Self = super().__new__(cls, BuildableFlagType.NotBuildable)
        return this
    def __init__(self, cell_id: int = 36):
        super().__init__(CellType.park,cell_id,"공원")

    @property
    @override
    def mandatoryPaymentInfos(self) -> Sequence[AbstractPaymentType]:
        return []
    @property
    @override
    def optionalPaymentInfos(self) -> Sequence[AbstractPaymentType]:
        return []
    
    @override
    def passing(self, state: GameStateType, player_icon: PlayerIconType) -> GameStateType:
        return state
    
    @override
    def arrived(self, state: GameStateType, player_now_icon: PlayerIconType, callback: Callable[[GameStateType], None]) -> tuple[GameStateType, Sequence[AbstractPaymentType]]:
        return (state, [])
    
    @property
    @override
    def hasEffectWhenPassing(self) -> bool:
        return False

class University(AbstractCellData):
    def __new__(cls):
        this: Self = super().__new__(cls, BuildableFlagType.NotBuildable)
        return this
    def __init__(self, cell_id: int = 18):
        super().__init__(CellType.university,cell_id,"대학")

    @property
    @override
    def mandatoryPaymentInfos(self) -> Sequence[AbstractPaymentType]:
        return []
    
    @property
    @override
    def optionalPaymentInfos(self) -> Sequence[AbstractPaymentType]:
        return []
    
    @override
    def passing(self, state: GameStateType, player_now_icon: PlayerIconType) -> GameStateType:
        return state
    
    @override
    def arrived(self, state: GameStateType, player_now_icon: PlayerIconType, callback: Callable[[GameStateType], None]) -> tuple[GameStateType, Sequence[AbstractPaymentType]]:
        new_state = universityAction(state,player_now_icon)
        callback(new_state)
        return (new_state, [])
    
    @property
    @override
    def hasEffectWhenPassing(self) -> bool:
        return False

class Jail(AbstractCellData):
    def __new__(cls):
        this: Self = super().__new__(cls, BuildableFlagType.NotBuildable)
        cls._payment_infos: Sequence[AbstractPaymentType] = [
            UnidirectionalPayment("P2G",400000)
        ]
        return this
    def __init__(self, cell_id: int = 9):
        super().__init__(CellType.jail,cell_id,"감옥")
    
    @property
    @override
    def mandatoryPaymentInfos(self) -> Sequence[AbstractPaymentType]:
        return []
    
    @property
    @override
    def optionalPaymentInfos(self) -> Sequence[AbstractPaymentType]:
        return Jail._payment_infos
    
    @override
    def passing(self, state: GameStateType, player_now_icon: PlayerIconType) -> GameStateType:
        return state
    
    @override
    def arrived(self, state: GameStateType, player_now_icon: PlayerIconType, callback: Callable[[GameStateType], None]) -> tuple[GameStateType, Sequence[AbstractPaymentType]]:
        return (imprisonment(state,player_now_icon), [])
    
    @property
    @override
    def hasEffectWhenPassing(self) -> bool:
        return False

class Start(AbstractCellData):
    def __new__(cls):
        this = super().__new__(cls, BuildableFlagType.NotBuildable)
        cls._salery_info = UnidirectionalPayment("M2P", 4000000)
        cls._taxes_info = UnidirectionalPayment("P2G", 1000000)
        return this
    def __init__(self):
        super().__init__(CellType.start,0,"출발")
    
    @property
    @override
    def mandatoryPaymentInfos(self) -> Sequence[AbstractPaymentType]:
        return [Start._salery_info, Start._taxes_info]
    
    @property
    @override
    def optionalPaymentInfos(self) -> Sequence[AbstractPaymentType]:
        return []

    @staticmethod
    def _getSalery(state: GameStateType, player_now_icon: PlayerIconType, salary_payments: Sequence[AbstractPaymentType]) -> GameStateType:
        count = min(len(state.players),4)
        if count >= 2 and count <= 4:
            transactor = UnidirectionalTransactor(player_now_icon)
            merged = mergeTransactions(map(transactor.transact,salary_payments))
            tmp = merged.toAppliedState(state)
            new_state = distributeBasicIncome(tmp)
            return new_state
        else:
            return state


    @override
    def passing(self, state: GameStateType, player_now_icon: PlayerIconType) -> GameStateType:
        return Start._getSalery(state,player_now_icon,self.mandatoryPaymentInfos)
    
    @override
    def arrived(self, state: GameStateType, player_now_icon: PlayerIconType, callback: Callable[[GameStateType], None]) -> tuple[GameStateType, Sequence[AbstractPaymentType]]:
        return (Start._getSalery(state,player_now_icon,self.mandatoryPaymentInfos), [])
    
    @property
    @override
    def hasEffectWhenPassing(self) -> bool:
        return True

class Concert(AbstractCellData):
    def __new__(cls):
        this: Self = super().__new__(cls, BuildableFlagType.NotBuildable)
        cls._payment_infos = [
            UnidirectionalPayment("P2M", 2000000),
            UnidirectionalPayment("P2G", 2000000),
            UnidirectionalPayment("P2C", 2000000)
        ]
        return this
    def __init__(self, cell_id: int = 27):
        super().__init__(CellType.concert,cell_id,"콘서트 (feat. IU)")
    
    @property
    @override
    def mandatoryPaymentInfos(self) -> Sequence[AbstractPaymentType]:
        return Concert._payment_infos
    
    @property
    @override
    def optionalPaymentInfos(self) -> Sequence[AbstractPaymentType]:
        return []

    @override
    def passing(self, state: GameStateType, player_now_icon: PlayerIconType) -> GameStateType:
        return state
    
    @override
    def arrived(self, state: GameStateType, player_now_icon: PlayerIconType, callback: Callable[[GameStateType], None]) -> tuple[GameStateType, Sequence[AbstractPaymentType]]:
        transactor = UnidirectionalTransactor(player_now_icon)
        merged = mergeTransactions(map(transactor.transact,self.mandatoryPaymentInfos))
        new_state = merged.toAppliedState(state)
        return (new_state, [])
        
    
    @property
    @override
    def hasEffectWhenPassing(self) -> bool:
        return False

class Industrial(AbstractCellData):
    def __new__(cls):
        this: Self = super().__new__(cls,BuildableFlagType.NotBuildable)
        cls._mandatory_payment_info = UnidirectionalPayment("P2G",600000)
        cls._optional_payment_info = P2DPayment(300000)
        return this

    def __init__(self, kind: str):
        (_cellId, _name) = CellNameLookups.industrial(kind)
        super().__init__(CellType.infrastructure,_cellId, _name)

    @property
    @override
    def mandatoryPaymentInfos(self) -> Sequence[AbstractPaymentType]:
        return [Industrial._mandatory_payment_info]
    
    @property
    @override
    def optionalPaymentInfos(self) -> Sequence[AbstractPaymentType]:
        return [Industrial._optional_payment_info]

    @override
    def passing(self, state: GameStateType, player_now_icon: PlayerIconType) -> GameStateType:
        return state
    
    @override
    def arrived(self, state: GameStateType, player_now_icon: PlayerIconType, callback: Callable[[GameStateType], None]) -> tuple[GameStateType, Sequence[AbstractPaymentType]]:
        transactor = UnidirectionalTransactor(player_now_icon)
        merged_mandatory = mergeTransactions(map(transactor.transact,self.mandatoryPaymentInfos))
        if self.cellId in state.properties.keys():
            p2d_transactor = P2DTransactor(player_now_icon,state.properties[self.cellId].ownerIcon,min(4,max(2,len(state.players))))
            merged_p2d = mergeTransactions(map(p2d_transactor.transact,self.optionalPaymentInfos))
            new_state = (merged_mandatory+merged_p2d).toAppliedState(state)
            callback(new_state)
            return (new_state, [])
        else:
            new_state = merged_mandatory.toAppliedState(state)
            callback(new_state)
            return (new_state, self.optionalPaymentInfos)
                
    
    @property
    @override
    def hasEffectWhenPassing(self) -> bool:
        return False

@dataclass
class CellNameLookupItemType(NamedTuple):
    cellId: int
    name: str

class CellNameLookups:
    def __new__(cls):
        cls._infrastructures: dict[str, CellNameLookupItemType] = {
            "water": CellNameLookupItemType(cellId=7, name="수자원"),
            "electricity": CellNameLookupItemType(cellId=16, name="전력"),
            "gas": CellNameLookupItemType(cellId=21, name="도시가스"),
        }
        cls._infrastructure_kinds: set[str] = set[str](cls._infrastructures.keys())
        cls._industrials: dict[str, CellNameLookupItemType] = {
            "digital-complex": CellNameLookupItemType(cellId=44, name="지식정보단지"),
            "agriculture": CellNameLookupItemType(cellId=35, name="농공단지"),
            "factory": CellNameLookupItemType(cellId=35, name="산업단지")
        }
        cls._industrial_kinds: set[str] = set[str](cls._industrials.keys())
    
    @classmethod
    def infrastructure(cls, kind: str) -> tuple[int, str]:
        tmp = cls._infrastructures[kind]
        return (tmp.cellId, tmp.name)
    
    @classmethod
    def industrial(cls, kind: str) -> tuple[int, str]:
        tmp = cls._industrials[kind]
        return (tmp.cellId, tmp.name)
    
    @property
    @classmethod
    def infrastructure_kinds(cls) -> set[str]:
        return cls._infrastructure_kinds
    
    @property
    @classmethod
    def industrial_kinds(cls) -> set[str]:
        return cls._industrial_kinds
    
_TRANSPORTATIONS: list[Trnsportation] = list(map(lambda n: Trnsportation((n * 9 + 1), (((n+1)%6) * 9 + 1)),range(0,6)))
TRANSPORTATIONS: dict[int, Trnsportation] = {
    transportation.cellId: transportation for transportation in _TRANSPORTATIONS
}

LAND_DATA: list[list[tuple[int, str]]] = [
    [(2,"목포"), (4,"강릉")],
    [(6,"전주"), (8,"'포항")],
    [(11,"천안"), (12,"춘천"), (13,"청주")],
    [(15,"성남"), (17,"창원")],
    [(20,"진천"), (22,"음성")],
    [(24,"구미"), (25,"서산"), (26,"순천")],
    [(29,"고양"), (30,"울산")],
    [(32,"수원"), (33,"광주"), (34,"대전")],
    [(38,"포천"), (40,"양주")],
    [(42,"용인"), (43,"여수")],
    [(47,"대구"), (48,"인천"), (49,"제주")],
    [(51,"부산"), (53,"서울")]
]
_LANDS = list[tuple[int, Land]](map(
    lambda land: (land.cellId, land),
    reduce(
        lambda acc, curr: list[Land](acc + curr),
        list[list[Land]](map(
            lambda item: list[Land](map(
                lambda inner: Land(cell_id=inner[0],name=inner[1],group_factor=item[0] + 1),
                item[1]
            )),
            enumerate(LAND_DATA)
        )),
        list[Land]()
    )
))
LAND_CELL_IDS = reduce(lambda acc, curr: acc + curr,list(map(lambda inner: list[int](map(lambda item: item[0],inner)),LAND_DATA)),list[int]())
LANDS: dict[int, Land] = {
    cellId: land for cellId, land in _LANDS
}

CHANCES = {
    cellId: Chance(cell_id=cellId) for cellId in [5,14,23,31,41,50]
}

INFRASTRUCTURES_MAP = {
    infra.cellId: infra for infra in map(Infrastructure,CellNameLookups.infrastructure_kinds)
}

INDUSTRIALS_MAP = {
    industrial.cellId: industrial for industrial in map(Industrial,CellNameLookups.industrial_kinds)
}


OTHERS: dict[int,AbstractCellData] = {
    3: Lotto(),
    52: Charity(),
    0: Start(),
    9: Jail(),
    18: University(),
    27: Concert(),
    36: Park(),
    45: Hospital()
}


from utils import CellDictMerger


CELLS = CellDictMerger().merge(LANDS).merge(TRANSPORTATIONS).merge(CHANCES).merge(INFRASTRUCTURES_MAP).merge(INDUSTRIALS_MAP).merge(OTHERS).extract()

assert set(range(54)) == CELLS.keys()

def _getGroupCellIds(cellId: int) -> set[int]:
        group_factor = CELLS[cellId].group_factor
        filtered = dict(filter(lambda item: item[1].group_factor == group_factor,CELLS.items()))
        return set(copy.deepcopy(filtered.keys()))