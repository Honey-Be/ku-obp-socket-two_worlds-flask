from enum import Enum
from dataclasses import dataclass
from typing import NamedTuple, Literal, TypeVar, Generic, override, Union, Self, Optional, Iterable
from abc import ABCMeta, abstractmethod
from functools import reduce

import copy

INITIAL_CASH=6000000


boolLowercaseLiteral = Literal["true", "false"]
primitiveJSONItemType = int | float | boolLowercaseLiteral | str
listJSONType = list[primitiveJSONItemType]
complexJSONType = listJSONType | primitiveJSONItemType
completeJSONType = complexJSONType | dict[str, complexJSONType]
JSONType = completeJSONType | dict[str,completeJSONType]

class UniversityStateType(Enum):
    notYet = "notYet"
    undergraduate = "undergraduate"
    graduated = "graduated"

@dataclass
class TicketsType(NamedTuple):
    discountRent: int
    bonus: bool
    doubleLotto: int

class PlayerIconType(Enum):
    first = 0
    second = 1
    third = 2
    fourth = 3

def getNextIcon(icon: PlayerIconType, players_count: Literal[2, 3, 4]) -> PlayerIconType:
    tmp = icon.value + 1
    output = tmp % players_count
    return PlayerIconType(output)


class DiceType(Enum):
    Null = 0
    OneOne = 1
    OneTwo = 2
    OneThree = 3
    OneFour = 4
    OneFive = 5
    OneSix = 6
    TwoOne = 7
    TwoTwo = 8
    TwoThree = 9
    TwoFour = 10
    TwoFive = 11
    TwoSix = 12
    ThreeOne = 13
    ThreeTwo = 14
    ThreeThree = 15
    ThreeFour = 16
    ThreeFive = 17
    ThreeSix = 18
    FourOne = 19
    FourTwo = 20
    FourThree = 21
    FourFour = 22
    FourFive = 23
    FourSix = 24
    FiveOne = 25
    FiveTwo = 26
    FiveThree = 27
    FiveFour = 28
    FiveFive = 29
    FiveSix = 30
    SixOne = 31
    SixTwo = 32
    SixThree = 33
    SixFour = 34
    SixFive = 35
    SixSix = 36



DOUBLE_DICES: set[DiceType] = {
    DiceType.OneOne,
    DiceType.TwoTwo,
    DiceType.ThreeThree,
    DiceType.FourFour,
    DiceType.FiveFive,
    DiceType.SixSix
}

@dataclass
class PlayerMetadataType(NamedTuple):
    enterNum: int
    email: str
    icon: PlayerIconType


@dataclass
class PlayerType(NamedTuple):
    icon: PlayerIconType
    location: int
    displayLocation: int
    cash: int
    cycles: int
    university: UniversityStateType
    tickets: TicketsType
    remainingJailTurns: int

@dataclass
class PropertyType(NamedTuple):
    ownerIcon: PlayerIconType
    count: int

@dataclass
class SidecarType(NamedTuple):
    limitRents: int

@dataclass
class GameStateType(NamedTuple):
    roomId: str
    players: list[PlayerType]
    properties: dict[int,PropertyType]
    nowInTurn: PlayerIconType
    govIncome: int
    charityIncome: int
    diceCache: DiceType
    doublesCount: int

class PaymentTransaction:
    def __init__(self,
        first: int,
        second: int,
        third: int,
        fourth: int,
        government: int,
        charity: int
    ):
        self.first: int = first
        self.second: int = second
        self.third: int = third
        self.fourth: int = fourth
        self.government: int = government
        self.charity: int = charity

    def __add__(self, other):
        return PaymentTransaction(
            first=self.first + other.first,
            second=self.second + other.second,
            third=self.third + other.third,
            fourth=self.fourth + other.fourth,
            government=self.government + other.government,
            charity=self.charity + other.charity
        )
    
    def __sub__(self, other):
        return PaymentTransaction(
            first=self.first - other.first,
            second=self.second - other.second,
            third=self.third - other.third,
            fourth=self.fourth - other.fourth,
            government=self.government - other.government,
            charity=self.charity - other.charity
        )
    
    def __mul__(self, c: int):
        return PaymentTransaction(
            first=self.first * c,
            second=self.second * c,
            third=self.third * c,
            fourth=self.fourth * c,
            government=self.government * c,
            charity=self.charity * c
        )
    
    def __rmul__(self, c: int):
        return PaymentTransaction(
            first=self.first * c,
            second=self.second * c,
            third=self.third * c,
            fourth=self.fourth * c,
            government=self.government * c,
            charity=self.charity * c
        )
    
    def __neg__(self) -> Self:
        return PaymentTransaction(
            first = (-self.first),
            second = (-self.second),
            third = (-self.third),
            fourth = (-self.fourth),
            government = (-self.government),
            charity = (-self.charity)
        )
    
    @classmethod
    def blank(cls) -> Self:
        return PaymentTransaction(
            first=0,
            second=0,
            third=0,
            fourth=0,
            government=0,
            charity=0
        )
    
    def toDict(self) -> dict[str, int]:
        return {
            "player0": self.first,
            "player1": self.second,
            "player2": self.third,
            "player3": self.fourth,
            "government": self.government,
            "charity": self.charity
        }
    
    @classmethod
    def fromDict(cls, d: dict[str, int]) -> Self:
        return PaymentTransaction(
            first=d["player0"],
            second=d["player1"],
            third=d["player2"],
            fourth=d["player3"],
            government=d["government"],
            charity=d["charity"]
        )
    @classmethod
    def fromArray(cls, _players: list[int], government: int = 0, charity: int = 0) -> Self:
        players: list[int] = (_players + [0,0,0,0])[0:4]
        return PaymentTransaction(players[0],players[1], players[2], players[3], government,charity)
    
    def toAppliedPlayer(self, player_status: PlayerType) -> PlayerType:
        if player_status.icon == 0:
            selected = self.first
        elif player_status.icon == 1:
            selected = self.second
        elif player_status.icon == 2:
            selected = self.third
        else:
            selected = self.fourth
        
        new_player_status = PlayerType(player_status.icon,player_status.location,player_status.displayLocation,player_status.cash + selected,
                                       player_status.cycles,player_status.university,player_status.tickets,player_status.remainingJailTurns)
        return new_player_status
            
    def toAppliedState(self, state: GameStateType) -> GameStateType:
        _govIncome = state.govIncome + self.government
        _charityIncome = state.charityIncome + self.charity
        tmp = GameStateType(state.roomId,copy.deepcopy(state.players),copy.deepcopy(state.properties),state.nowInTurn,_govIncome,_charityIncome, state.diceCache, state.doublesCount)
        mapped = map(self.toAppliedPlayer,tmp.players)
        new_state = GameStateType(tmp.roomId,list(mapped),tmp.properties,tmp.nowInTurn,tmp.govIncome,tmp.charityIncome, tmp.diceCache, tmp.doublesCount)
        return new_state
    
    @classmethod
    def distribute(cls, amount_per_each: int, players_count: int) -> Self:
        return PaymentTransaction.fromArray([amount_per_each]*players_count)
            



def mergeTransactions(transactions: Iterable[PaymentTransaction]):
    merged = reduce(lambda acc, curr: acc + curr,transactions,PaymentTransaction.blank())
    return merged





UnidirectionalPaymentKind = Literal["P2M", "P2G", "P2C", "M2P", "G2P", "C2P"]
P2PPaymentKind = Literal["P2P"]
P2OPaymentKind = Literal["P2O"]
P2DPaymentKind = Literal["P2D"]
MarketGovPaymentKind = Literal["G2M", "M2G"]

PK = TypeVar("PK", UnidirectionalPaymentKind, P2PPaymentKind, P2OPaymentKind, MarketGovPaymentKind, P2DPaymentKind)
class AbstractPaymentType(Generic[PK], metaclass=ABCMeta):
    def __init__(self, kind: PK, cost: int):
        self._kind: PK = kind
        self._cost: int = cost
    
    @property
    def kind(self) -> PK:
        return self._kind

    @property
    def cost(self) -> int:
        return self._cost
 
class UnidirectionalPayment(AbstractPaymentType[UnidirectionalPaymentKind]):
    def __init__(self, kind: UnidirectionalPaymentKind, cost: int):
        super().__init__(kind, cost)
    
class P2PPayment(AbstractPaymentType[P2PPaymentKind]):
    def __init__(self, cost: int):
        super().__init__("P2P", cost)

class P2OPayment(AbstractPaymentType[P2OPaymentKind]):
    def __init__(self, cost: int):
        super().__init__("P2O", cost)

class P2DPayment(AbstractPaymentType[P2DPaymentKind]):
    def __init__(self, cost: int):
        super().__init__("P2D", cost)

class MarketGovPayment(AbstractPaymentType[MarketGovPaymentKind]):
    def __init__(self, kind: MarketGovPaymentKind, cost: int):
        super().__init__(kind, cost)


P = TypeVar("P", UnidirectionalPaymentKind, P2PPaymentKind, P2OPaymentKind, MarketGovPaymentKind, P2DPaymentKind)
class AbstractTransactor(Generic[P], metaclass=ABCMeta):
    @abstractmethod
    def transact(self, payment: AbstractPaymentType[P]) -> PaymentTransaction: pass

class UnidirectionalTransactor(AbstractTransactor[UnidirectionalPaymentKind]):
    def __init__(self, my_icon: PlayerIconType):
        self.my_icon: PlayerIconType = my_icon

    @override
    def transact(self, payment: AbstractPaymentType[UnidirectionalPaymentKind]) -> PaymentTransaction:
        if payment.kind == "P2C":
            tmp: list[int] = [0,0,0,0]
            tmp[self.my_icon.value] = -payment.cost
            return PaymentTransaction.fromArray(tmp,0,payment.cost)
        elif payment.kind == "C2P":
            tmp: list[int] = [0,0,0,0]
            tmp[self.my_icon.value] = payment.cost
            return PaymentTransaction.fromArray(tmp,0,-payment.cost)
        elif payment.kind == "P2G":
            tmp: list[int] = [0,0,0,0]
            tmp[self.my_icon.value] = -payment.cost
            return PaymentTransaction.fromArray(tmp,payment.cost,0)
        elif payment.kind == "G2P":
            tmp: list[int] = [0,0,0,0]
            tmp[self.my_icon.value] = payment.cost
            return PaymentTransaction.fromArray(tmp,-payment.cost,0)
        elif payment.kind == "P2M":
            tmp: list[int] = [0,0,0,0]
            tmp[self.my_icon.value] = -payment.cost
            return PaymentTransaction.fromArray(tmp,0,0)
        else:
            tmp: list[int] = [0,0,0,0]
            tmp[self.my_icon.value] = payment.cost
            return PaymentTransaction.fromArray(tmp,0,0)
            

class P2PTransactor(AbstractTransactor[P2PPaymentKind]):
    def __init__(self, from_icon: PlayerIconType, to_icon: PlayerIconType):
        self.from_icon: PlayerIconType = from_icon
        self.to_icon: PlayerIconType = to_icon

    @override
    def transact(self, payment: AbstractPaymentType[P2PPaymentKind]) -> PaymentTransaction:
        tmp: list[int] = [0,0,0,0]
        tmp[self.from_icon.value] = -payment.cost
        tmp[self.to_icon.value] = payment.cost
        return PaymentTransaction.fromArray(tmp)

class P2OTransactor(AbstractTransactor[P2OPaymentKind]):
    def __init__(self, player_icon: PlayerIconType, owner_icon: PlayerIconType):
        self.player_icon: PlayerIconType = player_icon
        self.owner_icon: PlayerIconType = owner_icon

    @override
    def transact(self, payment: AbstractPaymentType[P2OPaymentKind]) -> PaymentTransaction:
        if self.player_icon == self.owner_icon:
            return PaymentTransaction.blank()
        else:
            tmp: list[int] = [0,0,0,0]
            tmp[self.player_icon.value] = -payment.cost
            tmp[self.owner_icon.value] = payment.cost
            return PaymentTransaction.fromArray(tmp)          

class P2DTransactor(AbstractTransactor[P2DPaymentKind]):
    def __init__(self, player_icon: PlayerIconType, owner_icon: PlayerIconType, players_count: int):
        self.player_icon: PlayerIconType = player_icon
        self.owner_icon: PlayerIconType = owner_icon
        self.players_count: int = min(max(players_count,2),4)

    @override
    def transact(self, payment: AbstractPaymentType[P2OPaymentKind]) -> PaymentTransaction:
        tmp: list[int] = ([(payment.cost // self.players_count)] * self.players_count)
        if self.player_icon == self.owner_icon:
            tmp[self.player_icon.value] = -((payment.cost // self.players_count) * (self.players_count - 1))
        else:
            tmp[self.player_icon.value] = -((payment.cost // self.players_count) * (self.players_count))
        return PaymentTransaction.fromArray(tmp)     

class MarketGovTransactor(AbstractTransactor[MarketGovPaymentKind]):
    @override
    def transact(self, payment: AbstractPaymentType[MarketGovPaymentKind]) -> PaymentTransaction:
        if payment.kind == "G2M":
            return PaymentTransaction.fromArray([],-payment.cost,0)
        else:
            return PaymentTransaction.fromArray([],payment.cost,0)
        
