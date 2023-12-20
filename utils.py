from hmac import new
from math import ceil, sqrt
import math
from operator import concat
from os import write
from time import sleep
from typing import AbstractSet, Any, Callable, Self, List, Sequence, overload

from click import prompt
from cells import AbstractCellData
from collections import UserDict
from collections.abc import MutableMapping

from kvsqlite.sync import Client

from ordered_set import OrderedSet

from random import gauss, shuffle
from chances import TYPHOON_TARGETS

from primitives import *

from flask_socketio import SocketIO,emit

import copy

import json as JSON

class PlayerSerializer:
    def __init__(self, playerState: PlayerType):
        self.icon: int = playerState.icon.value
        self.location: int = playerState.location
        self.displayLocation: int = playerState.displayLocation
        self.cash: float = playerState.cash
        self.cycles: int = playerState.cycles
        self.university: str = copy.deepcopy(playerState.university.value)
        self.ticketFeeExemption: int = playerState.tickets.feeExemption
        self.ticketTaxExemption: int = playerState.tickets.taxExemption
        self.ticketBonus: int = playerState.tickets.bonus
        self.ticketDoubleLotto: int = playerState.tickets.doubleLotto
        self.ticketLawyer: int = playerState.tickets.lawyer
        self.ticketFreeHospital: int = playerState.tickets.freeHospital
        self.remainingJailTurns: int = playerState.remainingJailTurns


class PropertyItemSerializer:
    def __init__(self, prop: PropertyType):
        self.ownerIcon: int = prop.ownerIcon.value
        self.count: int = prop.count


SLICE_ALL = slice(None)

from cells import *

def castIntToDice(raw: int) -> Literal[1,2,3,4,5,6]:
    if raw <= 1:
        return 1
    elif raw == 2:
        return 2
    elif raw == 3:
        return 3
    elif raw == 4:
        return 4
    elif raw == 5:
        return 5
    else:
        return 6


def safeConvertIntToDiceType(n: int) -> DiceType:
    if n < 1 or n > 36:
        return DiceType.Null
    else:
        return DiceType(n)


DICE_LOOKUP: dict[DiceType, tuple[Literal[1,2,3,4,5,6], Literal[1,2,3,4,5,6]] | tuple[Literal[0], Literal[0]]] = {
    DiceType.Null: (0,0),
    DiceType.OneOne: (1, 1),
    DiceType.OneTwo: (1, 2),
    DiceType.OneThree: (1, 3),
    DiceType.OneFour: (1, 4),
    DiceType.OneFive: (1, 5),
    DiceType.OneSix: (1, 6),
    DiceType.TwoOne: (2, 1),
    DiceType.TwoTwo: (2, 2),
    DiceType.TwoThree: (2, 3),
    DiceType.TwoFour: (2, 4),
    DiceType.TwoFive: (2, 5),
    DiceType.TwoSix: (2, 6),
    DiceType.ThreeOne: (3, 1),
    DiceType.ThreeTwo: (3, 2),
    DiceType.ThreeThree: (3, 3),
    DiceType.ThreeFour: (3, 4),
    DiceType.ThreeFive: (3, 5),
    DiceType.ThreeSix: (3, 6),
    DiceType.FourOne: (4, 1),
    DiceType.FourTwo: (4, 2),
    DiceType.FourThree: (4, 3),
    DiceType.FourFour: (4, 4),
    DiceType.FourFive: (4, 5),
    DiceType.FourSix: (4, 6),
    DiceType.FiveOne: (5, 1),
    DiceType.FiveTwo: (5, 2),
    DiceType.FiveThree: (5, 3),
    DiceType.FiveFour: (5, 4),
    DiceType.FiveFive: (5, 5),
    DiceType.FiveSix: (5, 6),
    DiceType.SixOne: (6, 1),
    DiceType.SixTwo: (6, 2),
    DiceType.SixThree: (6, 3),
    DiceType.SixFour: (6, 4),
    DiceType.SixFive: (6, 5),
    DiceType.SixSix: (6, 6)
}

VALID_DICE_LOOKUP: dict[DiceType, tuple[Literal[1,2,3,4,5,6], Literal[1,2,3,4,5,6]]] = {
    DiceType.OneOne: (1, 1),
    DiceType.OneTwo: (1, 2),
    DiceType.OneThree: (1, 3),
    DiceType.OneFour: (1, 4),
    DiceType.OneFive: (1, 5),
    DiceType.OneSix: (1, 6),
    DiceType.TwoOne: (2, 1),
    DiceType.TwoTwo: (2, 2),
    DiceType.TwoThree: (2, 3),
    DiceType.TwoFour: (2, 4),
    DiceType.TwoFive: (2, 5),
    DiceType.TwoSix: (2, 6),
    DiceType.ThreeOne: (3, 1),
    DiceType.ThreeTwo: (3, 2),
    DiceType.ThreeThree: (3, 3),
    DiceType.ThreeFour: (3, 4),
    DiceType.ThreeFive: (3, 5),
    DiceType.ThreeSix: (3, 6),
    DiceType.FourOne: (4, 1),
    DiceType.FourTwo: (4, 2),
    DiceType.FourThree: (4, 3),
    DiceType.FourFour: (4, 4),
    DiceType.FourFive: (4, 5),
    DiceType.FourSix: (4, 6),
    DiceType.FiveOne: (5, 1),
    DiceType.FiveTwo: (5, 2),
    DiceType.FiveThree: (5, 3),
    DiceType.FiveFour: (5, 4),
    DiceType.FiveFive: (5, 5),
    DiceType.FiveSix: (5, 6),
    DiceType.SixOne: (6, 1),
    DiceType.SixTwo: (6, 2),
    DiceType.SixThree: (6, 3),
    DiceType.SixFour: (6, 4),
    DiceType.SixFive: (6, 5),
    DiceType.SixSix: (6, 6)
}

DICE_REVERSE_LOOKUP: dict[tuple[Literal[1,2,3,4,5,6], Literal[1,2,3,4,5,6]],DiceType] = {
    (1, 1): DiceType.OneOne ,
    (1, 2): DiceType.OneTwo ,
    (1, 3): DiceType.OneThree ,
    (1, 4): DiceType.OneFour ,
    (1, 5): DiceType.OneFive ,
    (1, 6): DiceType.OneSix ,
    (2, 1): DiceType.TwoOne ,
    (2, 2): DiceType.TwoTwo ,
    (2, 3): DiceType.TwoThree ,
    (2, 4): DiceType.TwoFour ,
    (2, 5): DiceType.TwoFive ,
    (2, 6): DiceType.TwoSix ,
    (3, 1): DiceType.ThreeOne ,
    (3, 2): DiceType.ThreeTwo ,
    (3, 3): DiceType.ThreeThree ,
    (3, 4): DiceType.ThreeFour ,
    (3, 5): DiceType.ThreeFive ,
    (3, 6): DiceType.ThreeSix ,
    (4, 1): DiceType.FourOne ,
    (4, 2): DiceType.FourTwo ,
    (4, 3): DiceType.FourThree ,
    (4, 4): DiceType.FourFour ,
    (4, 5): DiceType.FourFive ,
    (4, 6): DiceType.FourSix ,
    (5, 1): DiceType.FiveOne ,
    (5, 2): DiceType.FiveTwo ,
    (5, 3): DiceType.FiveThree ,
    (5, 4): DiceType.FiveFour ,
    (5, 5): DiceType.FiveFive ,
    (5, 6): DiceType.FiveSix ,
    (6, 1): DiceType.SixOne ,
    (6, 2): DiceType.SixTwo ,
    (6, 3): DiceType.SixThree ,
    (6, 4): DiceType.SixFour ,
    (6, 5): DiceType.SixFive ,
    (6, 6): DiceType.SixSix ,
}


DOUBLE_DICES: set[DiceType] = {
    DiceType.OneOne,
    DiceType.TwoTwo,
    DiceType.ThreeThree,
    DiceType.FourFour,
    DiceType.FiveFive,
    DiceType.SixSix
}


class PlayerMetadataSet:
    def __init__(self, orig: Optional[Self] = None, *emails: str, shuffles: bool = False, isEnded: bool = False):
        super().__init__()
        if orig == None:
            result_emails: OrderedSet[str] = OrderedSet[str]([])
            result_icons: OrderedSet[PlayerIconType] = OrderedSet[PlayerIconType]([])
            result_metadata: list[PlayerMetadataType] = list([])
            filtered_emails = OrderedSet[str](emails).items[0:4]
            icons: list[PlayerIconType] = [PlayerIconType.first,PlayerIconType.second,PlayerIconType.third,PlayerIconType.fourth][0:len(filtered_emails)]
            if shuffles:
                shuffle(icons)

            for index, (email,icon) in enumerate(zip(filtered_emails,icons)):
                result_emails.add(email)
                result_icons.add(icon)
                result_metadata.append(PlayerMetadataType(index,email,icon))

            self._emails: OrderedSet[str] = copy.deepcopy(result_emails)
            self._icons: OrderedSet[PlayerIconType] = copy.deepcopy(result_icons)
            self._metadata: list[PlayerMetadataType] = copy.deepcopy(result_metadata)
            self._isEnded: bool = isEnded
        else:
            self._emails: OrderedSet[str] = copy.deepcopy(orig._emails)
            self._icons: OrderedSet[PlayerIconType] = copy.deepcopy(orig._icons)
            self._metadata: list[PlayerMetadataType] = copy.deepcopy(orig._metadata)
            self._isEnded: bool = copy.deepcopy(orig._isEnded)
        
    def has_emails(self,email: str):
        return self._emails.__contains__(email)

    def searchByIcon(self, icon: PlayerIconType) -> str:
        for pm in self._metadata:
            if pm.icon == icon:
                return pm.email
            else: continue
        else: return ""
        
    def searchByEmail(self, email: str) -> Optional[PlayerIconType]:
        for pm in self._metadata:
            if pm.email == email:
                return pm.icon
            else: continue
        else:
            return None
        
    def forEach(self, fn: Callable[[str,Literal[0,1,2,3]],None]):
        for pm in self._metadata:
            fn(pm.email, pm.icon.value)

    @property
    def size(self) -> int:
        return len(self._metadata)

    @property
    def host(self) -> PlayerMetadataType:
        return self._metadata[0]

    @property
    def isEnded(self) -> bool:
        return self._isEnded
    
    @isEnded.setter
    def isEnded(self, value: bool):
        self._isEnded = value

    def getPlayerEmailsList(self) -> list[str]:
        tmp = copy.deepcopy(self._metadata)
        cmp: Callable[[PlayerMetadataType], int] = lambda p: p.icon.value
        tmp.sort(key=cmp)
        return copy.deepcopy(list(map(lambda p: p.email, tmp)))


class CellDictMerger:
    def __init__(self, internal: dict[int,AbstractCellData] = {}):
        self._internal: dict[int,AbstractCellData] = internal
    def merge[C: AbstractCellData](self, d: dict[int,C]):
        new_internal = copy.deepcopy(self._internal)
        dkeys = filter(lambda key: key not in self._internal.keys(),d.keys())
        for key in dkeys:
            new_internal[key] = d[key]
        return CellDictMerger(new_internal)
    def extract(self):
        return copy.deepcopy(self._internal)



def serializePlayerMetadata(player_metadata: PlayerMetadataType) -> JSONType:
    return {
        "email": player_metadata.email,
        "icon": player_metadata.icon.value
    }





def serializeProperty(property: PropertyType) -> JSONType:
    return {
        "ownerIcon": property.ownerIcon.value,
        "count": property.count
    }


class PropertySerialized:
    def __init__(self, cellId: int, ownerIcon: int, count: int):
        self.cellId: int = cellId
        self.ownerIcon: int = ownerIcon
        self.count: int = count

    

class CellPromptType(Enum):
    tryLotto = "tryLotto"
    purchase = "purchase"
    jail = "jail"
    none = "none"
    trafficJam = "trafficJam"
    trade = "trade"
    extinction = "extinction"
    quickMove = "quickMove"
    greenNewDeal = "greenNewDeal"
    quirkOfFate = "quirkOfFate"
    sell = "sell"
    pickChance = "pickChance"
    normal = "normal"

class GameCache:
    def __init__(self, roomId: str, metadata: PlayerMetadataSet, player_states: list[PlayerType], properties: dict[int,PropertyType], nowInTurn: PlayerIconType, govIncome: int, charityIncome: int, diceCache: DiceType, doubles_count: int, remainingCatastropheTurns: int, remainingPandemicTurns: int, lottoSuccess: int, prompt: CellPromptType, usingDoubleLotto: bool = False, paymentChoicesCache: Sequence[AbstractPaymentType] = [], usePaymentChoicesCache: bool = False, duringMaintenance: bool = False, chanceCardDisplay: str = ""):
        self._roomId: str = copy.deepcopy(roomId)
        self._metadata: PlayerMetadataSet = copy.deepcopy(metadata)
        self._player_states: list[PlayerType] = copy.deepcopy(player_states)
        self._properties: dict[int,PropertyType] = copy.deepcopy(properties)
        self._nowInTurn: PlayerIconType = nowInTurn
        self._govIncome: int = govIncome
        self._charityIncome: int = charityIncome
        self._dice_cache: DiceType = diceCache
        self._doubles_count: int = doubles_count
        self._remainingCatastropheTurns: int = remainingCatastropheTurns
        self._remainingPandemicTurns: int = remainingPandemicTurns
        self._lottoSuccess: int = lottoSuccess
        self._prompt: CellPromptType = prompt
        self._usingDoubleLotto: bool = usingDoubleLotto
        self._paymentChoicesCache: Sequence[AbstractPaymentType] = paymentChoicesCache
        self._usePaymentChoicesCache: bool = usePaymentChoicesCache
        self._duringMaintenance: bool = duringMaintenance
        self._chanceCardDisplay: str = copy.deepcopy(chanceCardDisplay)

    @classmethod
    def initialize(cls, roomId: str, hostEmail: str, first_guestEmail: str, max_guests: Literal[1,2,3] = 3, shuffles: bool = False, *other_guestEmails: str):
        _metadata = PlayerMetadataSet(None,hostEmail,first_guestEmail,*other_guestEmails,shuffles=shuffles)
        tmp: list[PlayerIconType] = [PlayerIconType.first,PlayerIconType.second,PlayerIconType.third,PlayerIconType.fourth]
        _player_states: list[PlayerType] = list(map(lambda i: PlayerType(
            icon=i,
            location=0,
            displayLocation=0,
            cash=INITIAL_CASH,
            cycles=0,
            university=UniversityStateType.notYet,
            tickets=TicketsType(),
            remainingJailTurns=0
        ),tmp[0:_metadata.size]))
        _properties: dict[int,PropertyType] = {}
        return GameCache(roomId,_metadata,_player_states,_properties,PlayerIconType.first,0,0, DiceType.Null, 0,0, 0, 0, CellPromptType.normal)

    @property
    def roomId(self) -> str: return self._roomId

    @property
    def metadata(self) -> PlayerMetadataSet: return self._metadata

    @property
    def playerStates(self) -> list[PlayerType]: return self._player_states

    @property
    def properties(self) -> dict[int,PropertyType]: return self._properties

    @property
    def nowInTurn(self) -> PlayerIconType: return self._nowInTurn
    
    @property
    def nowInTurnEmail(self) ->str: return self._metadata.searchByIcon(self._nowInTurn)

    @property
    def govIncome(self) -> int: return self._govIncome

    @property
    def charityIncome(self) -> int: return self._charityIncome

    @property
    def diceCache(self) -> DiceType: return self._dice_cache
    
    @property
    def doublesCount(self) -> int: return self._doubles_count

    @property
    def remainingCatastropheTurns(self) -> int: return self._remainingCatastropheTurns

    @remainingCatastropheTurns.setter
    def remainingCatastropheTurns(self, value: int): self.remainingCatastropheTurns = value

    @property
    def remainingPandemicTurns(self) -> int: return self._remainingPandemicTurns

    @remainingPandemicTurns.setter
    def remainingPandemicTurns(self, value: int): self.remainingPandemicTurns = value

    @diceCache.setter
    def diceCache(self, value: DiceType): self._dice_cache = value

    @doublesCount.setter
    def doublesCount(self, value: int): self._doubles_count = value

    @metadata.setter
    def metadata(self,value: PlayerMetadataSet): self._metadata = value

    @playerStates.setter
    def playerStates(self,value: list[PlayerType]): self._player_states = value

    @properties.setter
    def properties(self,value: dict[int,PropertyType]): self._properties = value

    @nowInTurn.setter
    def nowInTurn(self,value: PlayerIconType): self._nowInTurn = value

    @govIncome.setter
    def govIncome(self,value: int): self._govIncome = value
    
    @charityIncome.setter
    def charityIncome(self,value: int): self._charityIncome = value

    @property
    def lottoSuccess(self) -> int: return self._lottoSuccess

    @lottoSuccess.setter
    def lottoSuccess(self, value: int): self._lottoSuccess = value

    @property
    def prompt(self) -> CellPromptType: return self._prompt

    @prompt.setter
    def prompt(self, value: CellPromptType): self._prompt = value

    def copy(self):
        return GameCache(self._roomId,self._metadata, self._player_states,self._properties,self._nowInTurn,self._govIncome,self._charityIncome, self._dice_cache, self._doubles_count, self._remainingCatastropheTurns, self._remainingPandemicTurns, self._lottoSuccess, self._prompt, self._usingDoubleLotto, copy.deepcopy(self._paymentChoicesCache),self._usePaymentChoicesCache,self._duringMaintenance)

    @property
    def usingDoubleLotto(self) -> bool: return self._usingDoubleLotto

    @usingDoubleLotto.setter
    def usingDoubleLotto(self, value: bool): self._usingDoubleLotto = value

    @property
    def gameState(self) -> GameStateType:
        output = GameStateType(
            roomId=copy.deepcopy(self._roomId),
            players=copy.deepcopy(self.playerStates),
            properties=copy.deepcopy(self.properties),
            nowInTurn=self.nowInTurn,
            govIncome=self.govIncome,
            charityIncome=self.charityIncome,
            diceCache=self.diceCache,
            doublesCount=self.doublesCount,
            remainingPandemicTurns=self.remainingPandemicTurns,
            remainingCatastropheTurns=self.remainingCatastropheTurns)
        return output
    
    @property
    def chanceCardDisplay(self) -> str: return self._chanceCardDisplay

    @chanceCardDisplay.setter
    def chanceCardDisplay(self, value: str): self._chanceCardDisplay = value


    def updateGameState(self, io: SocketIO) -> None:
        self._emitUpdateGameStateGlobally(io)
        io.emit("updateChanceCardDisplay", self.chanceCardDisplay, to=self.roomId,include_self=True)
        io.emit("updatePrompt",str(self.prompt.value),to=self.roomId,include_self=True)

    def _emitUpdateGameStateGlobally(self, io: SocketIO):
        payload_updatePlayerStates = [
            JSON.dumps(PlayerSerializer(playerState).__dict__) for playerState in self.playerStates
        ]
        io.emit("updatePlayerStates", payload_updatePlayerStates, to=self.roomId, include_self=True)

        cellIds = copy.deepcopy(list(self.properties.keys()))
        payload_updateProperties = { f"cell{cellId}": JSON.dumps(PropertyItemSerializer(propertyItem).__dict__) for (cellId, propertyItem) in self.properties.items() }
        io.emit("updateProperties", (cellIds, JSON.dumps(payload_updateProperties)), to=self.roomId, include_self=True)
        io.emit("updateOtherStates", (self.nowInTurn.value, self.govIncome, self.charityIncome, self.remainingCatastropheTurns, self.remainingPandemicTurns), to=self.roomId, include_self=True)

    def _emitRefreshGameState(self):
        payload_updatePlayerStates = [
            JSON.dumps(PlayerSerializer(playerState).__dict__) for playerState in self.playerStates
        ]
        emit("updatePlayerStates", payload_updatePlayerStates, broadcast=False)

        cellIds = copy.deepcopy(list(self.properties.keys()))
        payload_updateProperties = { f"cell{cellId}": JSON.dumps(PropertyItemSerializer(propertyItem).__dict__) for (cellId, propertyItem) in self.properties.items() }
        emit("updateProperties", (cellIds, JSON.dumps(payload_updateProperties)), broadcast=False)
        emit("updateOtherStates", (self.nowInTurn.value, self.govIncome, self.charityIncome, self.remainingCatastropheTurns, self.remainingPandemicTurns), broadcast=False)


    def commitGameState(self, state: Optional[GameStateType], io: SocketIO):
        if state is not None:
            self.playerStates = copy.deepcopy(state.playerStates)
            self.properties = copy.deepcopy(state.properties)
            self.nowInTurn = state.nowInTurn
            self.govIncome = state.govIncome
            self.charityIncome = state.charityIncome
            self.diceCache = state.diceCache
            self.doublesCount = state.doublesCount
        
        self.updateGameState(io)
        
        with Client("room.sqlite") as db:
            db.set(f"{self.roomId}",self)


    @classmethod
    def load(cls, roomId: str):
        with Client("room.sqlite") as db:
            if db.exists(f"{roomId}"):
                imported: GameCache = db.get(f"{roomId}")
                return imported
            else: return None
            
    def notifyRoomStatus(self, io: Optional[SocketIO]):
        playerEmails: list[str] = self.metadata.getPlayerEmailsList()
        isEnded: bool = self.metadata.isEnded
        if io is not None:
            io.emit("notifyRoomStatus", (playerEmails, JSON.dumps(isEnded)), to=self.roomId, include_self=True)
        else:
            emit("notifyRoomStatus", (playerEmails, JSON.dumps(isEnded)), broadcast=False)
        
    def endGame(self, io: SocketIO):
        self.metadata.isEnded = True
        with Client("room.sqlite") as db:
            db.set(f"{self.roomId}",self)

        self.notifyRoomStatus(io)

    def notifyLoad(self) -> None:
        self.notifyRoomStatus(None)
        state = self.gameState
        print(f"\n\n\n{state}\n\n\n")
        self._emitRefreshGameState()
        emit("updateDoublesCount",self.doublesCount,broadcast=False)
        emit("showDices",int(self.diceCache.value),broadcast=False)
        emit("updateChanceCardDisplay", self.chanceCardDisplay, broadcast=False)

    def flushDices(self, io: SocketIO, new_doubles_count: int):
        self.diceCache = DiceType.Null
        self.doublesCount = new_doubles_count
        io.emit("flushDices",to=self.roomId, include_self=True)

    def reportDices(self, dice1: Literal[1,2,3,4,5,6], dice2: Literal[1,2,3,4,5,6], io: SocketIO):
        self.diceCache = DICE_REVERSE_LOOKUP[(dice1, dice2)]
        io.emit("showDices", int(self.diceCache.value), to=self.roomId)
        
    def _garbageCollection(self):
        cellIds = copy.deepcopy(self.properties.keys())
        for cellId in cellIds:
            if self.properties[cellId].count <= 0:
                self.properties.pop(cellId)

    def _propertiesFilterForEach(self, f: Callable[[tuple[int, PropertyType]], bool], pipe: Callable[[PropertyType], PropertyType], *pipes: Callable[[PropertyType], PropertyType]):
        filtered = list(filter(f,self.properties.items()))
        for cellId, prop in filtered:
            resullt = reduce(lambda value,pipe: pipe(value),pipes,pipe(prop))
            self.properties[cellId] = copy.deepcopy(resullt)
        
    def _calculatePropertiesMaintenanceCost(self, f: Callable[[tuple[int, PropertyType]], bool]) -> Optional[int]:
        filtered = list(filter(f,self.properties.items()))
        result = reduce(lambda acc, _: acc + 1,filtered,0)
        if self.playerStates[self.nowInTurn.value].cash >= (100000 * result):
            return (result * 100000)
        else: return None

    def tryNextTurn(self, doubles: bool, io: SocketIO, skip: Literal[0,1,2,3] = 0) -> bool:
        location = (self.playerStates[self.nowInTurn.value].location) %  54
        inJail = (PREDEFINED_CELLS[location].cell_type == CellType.jail)
        if doubles and not inJail:
            self.flushDices(io,self.doublesCount + 1)
            return False
        else:
            self.flushDices(io, 0)
            triggerEndGame: bool = reduce(lambda acc, curr: acc and (curr.cycles >= 4),self.playerStates,True)
            if triggerEndGame:
                return True
            else:
                prevInTurn: Literal[0,1,2,3] = self.nowInTurn.value
                playersCount: Literal[2,3,4]
                if self.metadata.size >= 4:
                    playersCount = 4
                elif self.metadata.size <= 2: 
                    playersCount = 2
                else:
                    playersCount = 3
                nextInTurn: Literal[0,1,2,3] = (prevInTurn + 1 + skip) % playersCount
                self.nowInTurn = PlayerIconType(nextInTurn)
                if PREDEFINED_CELLS[self.playerStates[nextInTurn].location % 54].cell_type == CellType.jail and self.playerStates[nextInTurn].remainingJailTurns > 0:
                    self.prompt = CellPromptType.jail
                else:
                    self.prompt = CellPromptType.normal
                return False

    def tryJailExit(self, dices: DiceType, thanksToLawyer: bool = False) -> bool:
        if dices == DiceType.Null:
            if thanksToLawyer:
                lawyer = self.playerStates[self.nowInTurn.value].tickets.lawyer
                self.playerStates[self.nowInTurn.value].tickets.lawyer = max(0,lawyer - 1)
            else:
                cash: float = self.playerStates[self.nowInTurn.value].cash
                self.playerStates[self.nowInTurn.value].cash = max(0, cash - 400000)
            self.playerStates[self.nowInTurn.value].remainingJailTurns = 0
            return True
        else:
            if dices in DICE_REVERSE_LOOKUP:
                self.playerStates[self.nowInTurn.value].remainingJailTurns = 0
                return True
            else:
                rem: int = max(0,self.playerStates[self.nowInTurn.value].remainingJailTurns - 1)
                self.playerStates[self.nowInTurn.value].remainingJailTurns = rem
                return False

    def _buildableAmount(self, icon: PlayerIconType, location: int) -> Literal[0,1,2,3]:
        max_buildable = PREDEFINED_CELLS[location].maxBuildable.value
        if location in self.properties.keys():
            if self.properties[location].ownerIcon.value == icon.value:
                tmp: int = max_buildable - self.properties[location].count
                if tmp >= 3:
                    return 3
                elif tmp <= 0:
                    return 0
                elif tmp == 2:
                    return 2
                else:
                    return 1
            else:
                return BuildableFlagType.NotBuildable.value
        else:
            return max_buildable

    def construct(self, amount: Literal[1,2,3]):
        now_location: int = self.playerStates[self.nowInTurn.value].location % 54
        max_buildable = self._buildableAmount(self.nowInTurn,now_location)
        toConstruct = max(0,min(amount,max_buildable))
        new_count = self.properties[now_location].count + toConstruct
        self.properties[now_location].count = new_count

    def isDouble(self) -> bool:
        if self.diceCache in DOUBLE_DICES:
            return True
        else:
            return False
    
    def distributeBasicIncome(self):
        basicIncome = self.govIncome / self.metadata.size
        for i in range(len(self.playerStates)):
            new_cash = self.playerStates[i].cash + basicIncome
            self.playerStates[i].cash = new_cash
        self.govIncome = 0

    def giveSalery(self):
        

        freeTaxTicket = self.playerStates[self.nowInTurn.value].tickets.taxExemption
        if freeTaxTicket > 0:
            _addedCash = 6000000
            self.playerStates[self.nowInTurn.value].tickets.taxExemption = max(0,freeTaxTicket - 1)
        else:
            _addedCash = 3000000

        bonusTicket = self.playerStates[self.nowInTurn.value].tickets.bonus
        if bonusTicket > 0:
            addedCash = _addedCash * 2
            self.playerStates[self.nowInTurn.value].tickets.bonus = max(0,bonusTicket - 1)
        else:
            addedCash = _addedCash

        cash = self.playerStates[self.nowInTurn.value].cash + addedCash
        self.playerStates[self.nowInTurn.value].cash = cash
        
        if freeTaxTicket <= 0:
            govIncome = self.govIncome + 1000000
            self.govIncome = govIncome

        self.distributeBasicIncome()
        
    def transport(self):
        src = (self.playerStates[self.nowInTurn.value].location) % 54
        if PREDEFINED_CELLS[src].cell_type == CellType.transportation:
            self.playerStates[self.nowInTurn.value].location = TRANSPORTATIONS[src].dest

    def _chance_newborn(self): # 출산 ㅊㅋㅊㅋ : 시장으로부터 100만 받음
        after = self.playerStates[self.nowInTurn.value].cash + 1000000
        self.playerStates[self.nowInTurn.value].cash = after
        return True

    def _chance_earthquake(self): # 지진 : 자신의 집이 있는 모든 도시에 집 한채씩 파괴됩니다.
        self._propertiesFilterForEach(lambda pair: pair[1].ownerIcon == self.nowInTurn,
                                      lambda prop: PropertyType(prop.ownerIcon,max(0,prop.count - 1)))
        self._garbageCollection()
        return True

    def _chance_tax_heaven(self, io: SocketIO): # 조세회피처 [감옥으로 워프]
        self.warp(9,io,True)
        return True

    def _chance_disease(self, io: SocketIO): # 병원행 [병원으로 워프]
        self.warp(45,io,True)
        return True

    def _chance_emergency_aid(self, io: SocketIO): # 긴급의료비 지원 (병원비 1회 무료) [티켓]
        after = self.playerStates[self.nowInTurn.value].tickets.freeHospital + 1
        self.playerStates[self.nowInTurn.value].tickets.freeHospital = after
        return True

    def _chance_drug(self, io: SocketIO): # 마약 소지 적발 [감옥으로 워프]
        self.warp(9,io,True)
        return True

    def _chance_nursing(self, io: SocketIO): # 부모님 간호 [병원으로 워프]
        self.warp(45,io,True)
        return True

    def _chance_quirk_of_fate(self, io: SocketIO): # 운명의 장난 [주사위 굴리기 프롬프트]
        self.prompt = CellPromptType.quirkOfFate
        return True

    def _chance_inherit_get(self, io: SocketIO): # 유산 상속 (100만 get)
        new_cash = self.playerStates[self.nowInTurn.value].cash + 1000000
        self.playerStates[self.nowInTurn.value].cash = new_cash
        return True
    
    def _chance_inherit_donate(self, io: SocketIO): # 상속받은 유산 100만 기부
        after = self.playerStates[self.nowInTurn.value].cash - 1000000
        self.playerStates[self.nowInTurn.value].cash =  after

        if after < 0:
            self._trigger_sell(io,False)

        return True

    def _chance_maintenance(self, io: SocketIO): # 건물 유지보수 (건물 한 채당 10만씩)
        calculated: Optional[int] = self._calculatePropertiesMaintenanceCost(lambda item: item[1].ownerIcon == self.nowInTurn)
        if calculated is None:
            self._trigger_sell(io,False,True)
        return True

    def _chance_healthy(self, io: SocketIO): # 건강한 식습관 (병원비 1회 무료) [티켓]
        after = self.playerStates[self.nowInTurn.value].tickets.freeHospital + 1
        self.playerStates[self.nowInTurn.value].tickets.freeHospital = after

        return True

    def _chance_cyber_security_threat(self, io: SocketIO): # 사이버 범죄 (시장에 100만 지불)
        after = self.playerStates[self.nowInTurn.value].cash - 1000000
        self.playerStates[self.nowInTurn.value].cash =  after

        if after < 0:
            self._trigger_sell(io,False)

        return True

    def _chance_typhoon(self, io: SocketIO): # 태풍 : 해안 도시(목포, 강릉, 포항, 순천, 제주 , 울산, 인천, 부산, 창원, 서산, 순천, 여수)에 있는 건물이 한 채씩 파괴됩니다.
        for target in TYPHOON_TARGETS:
            if target in list(self.properties.keys()):
                after = self.properties[target].count - 1
                self.properties[target].count = max(0,after)
        self._garbageCollection()

    def _chance_pandemic(self, io: SocketIO): # 팬데믹 : 1턴 동안 모든 사용료(토지, 건물, 서비스)가 면제됩니다. [사이드카]
        after = self.remainingPandemicTurns + len(self.playerStates)
        self.remainingPandemicTurns = after

        return True

    def _chance_fake_news(self, io: SocketIO): # 가짜뉴스에 대항할 이미지 메이킹 (시장에 100만 지불)
        after = self.playerStates[self.nowInTurn.value].cash - 1000000
        self.playerStates[self.nowInTurn.value].cash =  after

        if after < 0:
            self._trigger_sell(io,False)

        return True

    def _chance_green_new_deal(self, io: SocketIO): # 그린뉴딜 : 자신의 건물이 지어진 도시 한 곳에 무료로 건물을 1채 더 짓습니다.
        filtered = list(filter(lambda p: p[1].ownerIcon == self.nowInTurn,self.properties.items()))
        if len(filtered) > 0:
            self.prompt = CellPromptType.greenNewDeal
            return True
        else:
            return False
        
    def _chance_voice_phishing(self, io: SocketIO): # 보이스피싱 (시장에 100만 지불)
        after = self.playerStates[self.nowInTurn.value].cash - 1000000
        self.playerStates[self.nowInTurn.value].cash =  after

        if after < 0:
            self._trigger_sell(io,False)

        return True

    def _chance_scholarship(self, io: SocketIO): # 장학금 [대학으로 워프]
        self.warp(18,io,True)
        return True

    def _chance_catastrophe(self, io: SocketIO): # 긴급재난 발생 : 대도시(서울, 부산, 인천, 대구, 대전, 광주, 울산, 창원, 고양, 수원)에 긴급재난이 발생했습니다. [지역 한정 사이드카]
        after = self.remainingCatastropheTurns + len(self.playerStates)
        self.remainingCatastropheTurns = after
        return True

    def _chance_fee_exemption(self, io: SocketIO): # 토지 및 건물 사용료 면제 [티켓]
        after = self.playerStates[self.nowInTurn.value].tickets.feeExemption + 1
        self.playerStates[self.nowInTurn.value].tickets.feeExemption = after
        return True

    def _chance_bonus(self, io: SocketIO): # 보너스 지급 : 다음 차례 출발지 도착/경유 시 2배의 급여를 받습니다.
        after = self.playerStates[self.nowInTurn.value].tickets.bonus + 1
        self.playerStates[self.nowInTurn.value].tickets.bonus = after
        return True

    def _chance_doubleLotto(self, io: SocketIO): # 더블 로또 [티켓]
        after = self.playerStates[self.nowInTurn.value].tickets.doubleLotto + 1
        self.playerStates[self.nowInTurn.value].tickets.doubleLotto = after
        return True

    def _chance_insider_trading(self, io: SocketIO): # 내부자 거래 적발 [감옥으로 워프]
        self.warp(9,io,True)
        return True

    def _chance_traffic_jam(self, io: SocketIO): # 교통체증 : 원하는 도시의 건물 한 채 제거
        filtered = list(filter(lambda p: p[1].ownerIcon != self.nowInTurn,self.properties.items()))
        if len(filtered) > 0:
            self.prompt = CellPromptType.trafficJam
            return True
        else:
            return False

    def _chance_quick_move(self, io: SocketIO): # 원하는 곳으로 이동(워프 아님!!)
        self.prompt = CellPromptType.quickMove
        return True

    def _chance_traffic_accident(self, io: SocketIO): # 교통사고 (시장에 50만 지불)
        after = self.playerStates[self.nowInTurn.value].cash - 500000
        self.playerStates[self.nowInTurn.value].cash =  after

        if after < 0:
            self._trigger_sell(io,False)

        return True

    def _chance_tax_exemption(self, io: SocketIO): # 다음 차례 출발점 도착/경유 시 공과금(물, 전기, 도시가스) 면제
        after = self.playerStates[self.nowInTurn.value].tickets.taxExemption + 1
        self.playerStates[self.nowInTurn.value].tickets.taxExemption = after
        return True

    def _chance_too_much_electrivity(self, io: SocketIO): # [전력회사로 워프]
        self.warp(16,io,True)
        return True

    def _chance_lawyers_help(self, io: SocketIO): # 변호사 : 즉시 감옥에서 석방 [티켓]
        after = self.playerStates[self.nowInTurn.value].tickets.lawyer + 1
        self.playerStates[self.nowInTurn.value].tickets.lawyer = after
        return True

    def _chance_soaring_stock_price(self, io: SocketIO): # 주식시장 급등 : 보유한 현금의 50%를 시장에서 받습니다. (현금 끝자리 5만일 경우 반올림)
        profit = round(self.playerStates[self.nowInTurn.value].cash / 2,-5)
        after = self.playerStates[self.nowInTurn.value].cash + profit
        self.playerStates[self.nowInTurn.value].cash = after
        return True

    def _chance_plunge_in_stock_price(self, io: SocketIO): # 주식시장 급등 : 현금자산의 절반을 잃습니다. (시장에 지불, 현금 끝자리 5만일 경우 반올림)
        loss = round(self.playerStates[self.nowInTurn.value].cash / 2,-5)
        after = self.playerStates[self.nowInTurn.value].cash - loss
        self.playerStates[self.nowInTurn.value].cash = after
        return True

    def _chance_studying_hard(self, io: SocketIO): # 주경야독으로 학위 취득 성공 : 즉시 졸업
        if self.playerStates[self.nowInTurn.value].university != UniversityStateType.graduated:
            self.playerStates[self.nowInTurn.value].university = UniversityStateType.graduated
            return True
        else:
            return False

    def _chance_extinction(self, io: SocketIO): # 지방 소멸 : 한 그룹의 도시들을 선택합니다. 해당 그룹의 모든 도시에 있는 집을 1채 씩 없앱니다
        self.prompt = CellPromptType.extinction
        return True

    def _chance_trade(self, io: SocketIO): # 도시 교환 : 자신의 도시 1개와 원하는 (상대방의) 도시 1개를 선택하여 통째로 맞교환합니다.
        owners = set(map(lambda p: p[1].ownerIcon,self.properties.items()))
        
        if self.nowInTurn in owners and len(owners) > 1:
            self.prompt = CellPromptType.trade
            return True
        else:
            return False

    def _trigger_sell(self, io: SocketIO, usePatmentChoicesCache: bool, duringMaintenance: bool = False):
        self.prompt = CellPromptType.sell
        self._usePaymentChoicesCache = usePatmentChoicesCache
        self._duringMaintenance = duringMaintenance
        self.commitGameState(None, io)

    def getChance(self, io: SocketIO):
        src = (self.playerStates[self.nowInTurn.value].location) % 54

        if PREDEFINED_CELLS[src].cell_type == CellType.chance:
            while True:
                picked = choice(list(CHANCE_CARDS))
                self.chanceCardDisplay = copy.deepcopy(picked)
                if picked == "newborn":
                    result = self._chance_newborn()
                elif picked == "earthquake":
                    result = self._chance_earthquake()
                elif picked == "tax-heaven":
                    result = self._chance_tax_heaven(io)
                elif picked == "disease":
                    result = self._chance_disease(io)
                elif picked == "emergency-aid":
                    result = self._chance_emergency_aid(io)
                elif picked == "drug":
                    result = self._chance_drug(io)
                elif picked == "nursing":
                    result = self._chance_nursing (io)
                elif picked == "quirk-of-fate":
                    result = self._chance_quirk_of_fate(io)
                elif picked == "inherit-get":
                    result = self._chance_inherit_get(io)
                elif picked == "inherit-donate":
                    result = self._chance_inherit_donate(io)
                elif picked == "maintenance":
                    result = self._chance_maintenance(io)
                elif picked == "healthy":
                    result = self._chance_healthy(io)
                elif picked == "cyber-security-threat":
                    result = self._chance_cyber_security_threat(io)
                elif picked == "Typhoon":
                    result = self._chance_typhoon(io)
                elif picked == "pandemic":
                    result = self._chance_pandemic(io)
                elif picked == "fake-news":
                    result = self._chance_fake_news(io)
                elif picked == "green-new-deal":
                    result = self._chance_green_new_deal(io)
                elif picked == "voice-phishing":
                    result = self._chance_voice_phishing(io)
                elif picked == "scholarship":
                    result = self._chance_scholarship(io)
                elif picked == "catastrophe":
                    result = self._chance_catastrophe(io)
                elif picked == "fee-exemption":
                    result = self._chance_fee_exemption(io)
                elif picked == "bonus":
                    result = self._chance_bonus(io)
                elif picked == "doubleLotto":
                    result = self._chance_doubleLotto(io)
                elif picked == "insider-trading":
                    result = self._chance_insider_trading(io)
                elif picked == "traffic-jam":
                    result = self._chance_traffic_jam(io)
                elif picked == "quick-move":
                    result = self._chance_quick_move(io)
                elif picked == "traffic-accident":
                    result = self._chance_traffic_accident(io)
                elif picked == "tax-exemption":
                    result = self._chance_tax_exemption(io)
                elif picked == "too-much-electrivity":
                    result = self._chance_too_much_electrivity(io)
                elif picked == "lawyers-help":
                    result = self._chance_lawyers_help(io)
                elif picked == "soaring-stock-price":
                    result = self._chance_soaring_stock_price(io)
                elif picked == "plunge-in-stock-price":
                    result = self._chance_plunge_in_stock_price(io)
                elif picked == "studying-hard":
                    result = self._chance_studying_hard(io)
                elif picked == "extinction":
                    result = self._chance_extinction(io)
                elif picked == "trade":
                    result = self._chance_trade(io)
                else:
                    result = False
                if result:
                    break
                
    def checkActions(self, io: SocketIO, payment_choices: Sequence[AbstractPaymentType]) -> bool:
        location = self.playerStates[self.nowInTurn.value].location
        cell_type = PREDEFINED_CELLS[location].cell_type

        if cell_type == CellType.transportation:
            self.transport()
            return True
        elif cell_type == CellType.chance:
            self.prompt = CellPromptType.pickChance
        elif cell_type == CellType.charity or cell_type == CellType.concert or cell_type == CellType.jail or cell_type == CellType.infrastructure or cell_type == CellType.hospital:
            return True
        elif cell_type == CellType.industrial or cell_type == CellType.land:
            if len(payment_choices) > 0:
                self.prompt = CellPromptType.purchase
            else:
                return True
        elif cell_type == CellType.lotto:
            if self.lottoSuccess < 3:
                self.prompt = CellPromptType.tryLotto
        
        return False




    def go(self,amount: int, io: SocketIO) -> bool:
        src: int = self.playerStates[self.nowInTurn.value].location
        dest: int = (src + amount) % 54
        for n in range(1,amount+1):
            new_displayLocation = (src + n) % 54
            self.playerStates[self.nowInTurn.value].displayLocation = new_displayLocation
            if new_displayLocation == 0:
                self.giveSalery()
                new_cycles = self.playerStates[self.nowInTurn.value].cycles + 1
                self.playerStates[self.nowInTurn.value].cycles = new_cycles
            self.commitGameState(None, io)
            sleep(0.6)
        self.playerStates[self.nowInTurn.value].location = dest
        self.commitGameState(None, io)
        sleep(0.6)
        
        state_arrival = copy.deepcopy(self.gameState)
        (state_after, payment_choices) = PREDEFINED_CELLS[dest].arrived(state_arrival,self.nowInTurn)
        if (dest in CATASTROPHE_TARGETS and self.remainingCatastropheTurns > 0) or self.remainingPandemicTurns > 0:
            turn_finished = self.checkActions(io, payment_choices)
            self.commitGameState(None, io)
        else:
            self.commitGameState(state_after, io)
            if self.playerStates[self.nowInTurn.value].cash >= 0:
                turn_finished = self.checkActions(io, payment_choices)
                self.commitGameState(None, io)
            else:
                self.prompt = CellPromptType.sell
                self._paymentChoicesCache = copy.deepcopy(payment_choices)
                self.commitGameState(None, io)
                turn_finished = False
        sleep(0.6)
        return turn_finished

    def goBack(self, amount: int, io: SocketIO) -> bool:
        src: int = self.playerStates[self.nowInTurn.value].location
        dest: int = (src - amount) % 54
        for n in range(1,amount+1):
            new_displayLocation = (src - n) % 54
            self.playerStates[self.nowInTurn.value].displayLocation = new_displayLocation
            self.commitGameState(None, io)
            sleep(0.6)
        self.playerStates[self.nowInTurn.value].location = dest
        self.commitGameState(None, io)
        state_arrival = copy.deepcopy(self.gameState)
        (state_after, payment_choices) = PREDEFINED_CELLS[dest].arrived(state_arrival,self.nowInTurn)
        if (dest in CATASTROPHE_TARGETS and self.remainingCatastropheTurns > 0) or self.remainingPandemicTurns > 0:
            turn_finished = self.checkActions(io, payment_choices)
            self.commitGameState(None, io)
        else:
            self.commitGameState(state_after, io)
            if self.playerStates[self.nowInTurn.value].cash >= 0:
                turn_finished = self.checkActions(io, payment_choices)
                self.commitGameState(None, io)
            else:
                self.prompt = CellPromptType.sell
                self._paymentChoicesCache = copy.deepcopy(payment_choices)
                self.commitGameState(None, io)
                turn_finished = False
        sleep(0.6)
        return turn_finished

    def warp(self, dest: int, io: SocketIO, do_arrival_action: bool = False):
        self.playerStates[self.nowInTurn.value].location = dest % 54

        if do_arrival_action:
            state_arrival = copy.deepcopy(self.gameState)
            (state_after, payment_choices) = PREDEFINED_CELLS[dest].arrived(state_arrival,self.nowInTurn)
            if (dest in CATASTROPHE_TARGETS and self.remainingCatastropheTurns > 0) or self.remainingPandemicTurns > 0:
                turn_finished = self.checkActions(io, payment_choices)
                self.commitGameState(None, io)
            else:
                self.commitGameState(state_after, io)
                if self.playerStates[self.nowInTurn.value].cash >= 0:
                    turn_finished = self.checkActions(io, payment_choices)
                    self.commitGameState(None, io)
                else:
                    self.prompt = CellPromptType.sell
                    self._paymentChoicesCache = copy.deepcopy(payment_choices)
                    self.commitGameState(None, io)
                    turn_finished = False
            sleep(0.6)
            return turn_finished
        else:
            self.commitGameState(None, io)
            sleep(0.6)
            return False


    def sellForDebt(self, target_location: int, amount: int, io: SocketIO):
        if (target_location % 54) not in self.properties.keys():
            return
        elif self.properties[target_location % 54].ownerIcon != self.nowInTurn:
            return

        sell_amount = min(self.properties[target_location % 54].count, amount)
        amount_after = self.properties[target_location % 54].count - sell_amount
        self.properties[target_location % 54].count = amount_after
        cash_after = self.playerStates[self.nowInTurn.value].cash + (sell_amount * 150000)
        self.playerStates[self.nowInTurn.value].cash = cash_after

        self._garbageCollection()
        self.commitGameState(None, io)
        
        if self._duringMaintenance:
            calculated: Optional[int] = self._calculatePropertiesMaintenanceCost(lambda item: item[1].ownerIcon == self.nowInTurn)
            if calculated is None:
                pass
            else:
                after = self.playerStates[self.nowInTurn.value].cash - calculated
                self.playerStates[self.nowInTurn.value].cash = after
                self.prompt = CellPromptType.none
        elif cash_after > 0:
            if self._usePaymentChoicesCache:
                payment_choices = copy.deepcopy(self._paymentChoicesCache)
                self._paymentChoicesCache = []
                self.checkActions(io, payment_choices)
            self.commitGameState(None, io)
            self._usePaymentChoicesCache = False
            self.prompt = CellPromptType.none
        else:
            remains = list(filter(lambda p: p[1].ownerIcon == self.nowInTurn, copy.deepcopy(self.properties.items())))
            if len(remains) <= 0:
                helpsWithCharity = cash_after + copy.deepcopy(self.charityIncome)
                self.playerStates[self.nowInTurn.value].cash = helpsWithCharity
                self.charityIncome = 0
                if helpsWithCharity < 0:
                    self.distributeBasicIncome()
                
    


def isPrimeInteger(num: int):
    if num == 1:
        return False
    elif num > 1:
        # check for factors
        for i in range(2,num // 2):
            if (num % i) == 0:
                return False
        else:
            return True
    else:
        return False




class Eisenstein:
    def __init__(self, real: int, omega: int):
        self._real: int = real
        self._omega: int = omega
    
    @property
    def real(self) -> int:
        return self._real
    
    @property
    def omega(self) -> int:
        return self._omega

    def __complex__(self) -> complex:
        real = self.real - (self.omega / 2)
        imag = (self.omega * sqrt(3)) / 2
        return (real + imag*1j)
    
    @classmethod
    def toEisenstein(cls, x: int):
        return Eisenstein(x,0)

    
    @overload
    def __add__(self, other: Self):
        ...

    @overload
    def __add__(self, other: int):
        ...

    def __add__(self, other):
        if isinstance(other,Eisenstein):
            return Eisenstein(self.real + other.real, self.omega + other.omega)
        else:
            return self + Eisenstein.toEisenstein(other)

    @overload
    def __radd__(self, other: Self):
        ...

    @overload
    def __radd__(self, other: int):
        ...
        
    def __radd__(self, other):
        if isinstance(other,Eisenstein):
            return Eisenstein(self.real + other.real, self.omega + other.omega)
        else:
            return Eisenstein.toEisenstein(other) + self
    
    def __neg__(self):
        return Eisenstein(-self.real, -self.omega)

    def __pos__(self):
        return self

    @overload
    def __sub__(self, other: Self):
        ...

    @overload
    def __sub__(self, other: int):
        ...

    def __sub__(self, other):
        if isinstance(other,Eisenstein):
            return Eisenstein(self.real - other.real, self.omega - other.omega)
        else:
            return self - Eisenstein.toEisenstein(other)
    
    @overload
    def __rsub__(self, other: Self):
        ...

    @overload
    def __rsub__(self, other: int):
        ...

    def __rsub__(self, other):
        if isinstance(other,Eisenstein):
            return Eisenstein(other.real - self.real, other.omega - self.omega)
        else:
            return Eisenstein.toEisenstein(other) - self
    
    @overload
    def __mul__(self, other: Self):
        ...

    @overload
    def __mul__(self, other: int):
        ...

    def __mul__(self, other):
        if isinstance(other, int):
            return Eisenstein(self.real * other, self.omega * other)
        elif isinstance(other, Eisenstein):
            real = self.real * other.real
            omega = (self.omega * other.real) + (self.real * other.omega)
            omegaSq = self.omega * other.omega
            return Eisenstein(real - omegaSq, omega - omegaSq)
        else:
            raise TypeError(f"Invalid operation: Eisenstein * {type(other)} -> Eisenstein")
        
    @overload
    def __rmul__(self, other: Self):
        ...

    @overload
    def __rmul__(self, other: int):
        ...

    def __rmul__(self, other):
        if isinstance(other, int):
            return Eisenstein(other * self.real, other * self.omega)
        elif isinstance(other, Eisenstein):
            real = other.real * self.real
            omega = (other.real * self.omega) + (other.omega * self.real)
            omegaSq = other.omega * self.omega
            return Eisenstein(real - omegaSq, omega - omegaSq)
        else:
            raise TypeError(f"Invalid operation: {type(other)} * Eisenstein -> Eisenstein")
                
    
    def conjugate(self):
        real = self.real
        omegaSq = self.omega
        return Eisenstein(real - omegaSq, -omegaSq)
    
    def twoNormSquare(self):
        return (self.real ** 2) - (self.real * self.omega) + (self.omega)
    
    def __abs__(self):
        return sqrt(self.twoNormSquare())
    
    def __eq__(self, other: Self) -> bool:
        return (self.real == other.real) and (self.omega == other.omega)
    
    @classmethod
    def w(cls, omega: int = 1):
        return Eisenstein(0,omega)

    @classmethod
    def specialPrimes(cls):
        return [
            Eisenstein(1,-1),
            Eisenstein(1,2),
            Eisenstein(-2,-1)
        ]
    
    def __hash__(self):
        return (self._real, self._omega).__hash__()

    def isPrime(self) -> bool:
        if self in Eisenstein.specialPrimes():
            return True
        elif self.omega == 0 and self.real == 0:
            return False
        elif self.omega == 0 and self.real != 0:
            return isPrimeInteger(self.real) and ((self.real % 3) == 2)
        elif self.omega != 0 and self.real == 0:
            return isPrimeInteger(self.omega) and ((self.omega % 3) == 2)
        else:
            absolutePrimeOmegaSquare = isPrimeInteger(self.real) and ((self.real % 3) == 2) and (self.real == self.omega)
            _search_for: set[Eisenstein] = {self, self.conjugate(), self * Eisenstein.w(), self * Eisenstein(-1,-1)}
            _neg_search_for = set(map(lambda x: -x, _search_for))
            search_for: set[int] = set(map(lambda x: x.twoNormSquare(),_search_for.union(_neg_search_for)))
            merger: Callable[[bool, int], bool] = lambda acc, curr: acc or (isPrimeInteger(curr) and (curr % 3 == 1))
            oneModuloThree = reduce(merger,search_for,False)
            return absolutePrimeOmegaSquare or oneModuloThree


