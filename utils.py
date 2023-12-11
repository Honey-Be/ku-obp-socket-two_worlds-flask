from typing import AbstractSet, Any, Callable, Self, List, Sequence, overload
from cells import AbstractCellData
from collections import UserDict
from collections.abc import MutableMapping

from kvsqlite.sync import Client

from ordered_set import OrderedSet

from random import shuffle

from primitives import *

from flask_socketio import SocketIO,emit

import copy

SLICE_ALL = slice(None)



class PlayerMetadataSet:
    def __init__(self, orig: Optional[Self] = None, *emails: str, shuffles: bool = False):
        super().__init__()
        if orig == None:
            result_emails: OrderedSet[str] = OrderedSet[str]([])
            result_icons: OrderedSet[PlayerIconType] = OrderedSet[PlayerIconType]([])
            result_metadata: OrderedSet[PlayerMetadataType] = OrderedSet[PlayerMetadataType]([])
            filtered_emails = OrderedSet[str](emails).items[0:4]
            icons: list[PlayerIconType] = [PlayerIconType.first,PlayerIconType.second,PlayerIconType.third,PlayerIconType.fourth][0:len(filtered_emails)]
            if shuffles:
                shuffle(icons)

            for index, (email,icon) in enumerate(zip(filtered_emails,icons)):
                result_emails.add(email)
                result_icons.add(icon)
                result_metadata.add(PlayerMetadataType(index,email,icon))

            self._emails: OrderedSet[str] = result_emails
            self._icons: OrderedSet[PlayerIconType] = result_icons
            self._metadata: OrderedSet[PlayerMetadataType] = result_metadata
        else:
            self._emails: OrderedSet[str] = orig._emails.copy()
            self._icons: OrderedSet[PlayerIconType] = orig._icons.copy()
            self._metadata: OrderedSet[PlayerMetadataType] = orig._metadata.copy()
        
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




class CellDictMerger:
    def __init__(self, internal: dict[int,AbstractCellData] = {}):
        self._internal: dict[int,AbstractCellData] = internal
    def merge[C: AbstractCellData](self, d: dict[int,C]) -> Self:
        new_internal = copy.copy(self._internal)
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



def serializePlayerStatus(player: PlayerType) -> JSONType:
    return {
        "location": player.location,
        "displayLocation": player.displayLocation,
        "cash": player.cash,
        "cycles": player.cycles,
        "university": player.university.value,
        "tickets": {
            "bonus": player.tickets.bonus,
            "doubleLotto": player.tickets.doubleLotto,
            "discountRent": player.tickets.discountRent
        },
        "remainingJailTurns": player.remainingJailTurns
    }

def serializeProperty(property: PropertyType) -> JSONType:
    return {
        "ownerIcon": property.ownerIcon.value,
        "count": property.count
    }



def serializeGameState(state: GameStateType) -> dict[str,str | list[JSONType] | dict[str,JSONType] | int]:
    return {
        "roomId": state.roomId,
        "players": [
            serializePlayerStatus(player) for player in state.players
        ],
        "properties": {
            str(item[0]): serializeProperty(item[1]) for item in state.properties.items()
        },
        "nowInTurn": state.nowInTurn.value,
        "govIncome": state.govIncome,
        "charityIncome": state.charityIncome,
        "diceCache": state.diceCache.value,
        "doublesCount": state.doublesCount
    }
    

class GameCache:
    def __init__(self, roomId: str, metadata: PlayerMetadataSet, player_states: list[PlayerType], properties: dict[int,PropertyType], nowInTurn: PlayerIconType, govIncome: int, charityIncome: int, diceCache: DiceType, doubles_count: int):
        self._roomId: str = copy.deepcopy(roomId)
        self._metadata: PlayerMetadataSet = copy.deepcopy(metadata)
        self._player_states: list[PlayerType] = copy.deepcopy(player_states)
        self._properties: dict[int,PropertyType] = copy.deepcopy(properties)
        self._nowInTurn: PlayerIconType = nowInTurn
        self._govIncome: int = govIncome
        self._charityIncome: int = charityIncome
        self._dice_cache: DiceType = diceCache
        self._doubles_count: int = doubles_count

    @classmethod
    def initialize(cls, roomId: str, hostEmail: str, first_guestEmail: str, max_guests: Literal[1,2,3] = 3, shuffles: bool = False, *other_guestEmails: str) -> Self:
        _metadata = PlayerMetadataSet(None,hostEmail,first_guestEmail,*other_guestEmails,shuffles=shuffles)
        tmp: list[PlayerIconType] = [PlayerIconType.first,PlayerIconType.second,PlayerIconType.third,PlayerIconType.fourth]
        _player_states: list[PlayerType] = list(map(lambda i: PlayerType(
            icon=i,
            location=0,
            displayLocation=0,
            cash=INITIAL_CASH,
            cycles=0,
            university=UniversityStateType.notYet,
            tickets=TicketsType(discountRent=0,bonus=False,doubleLotto=0),
            remainingJailTurns=0
        ),tmp[0:_metadata.size]))
        _properties: dict[int,PropertyType] = {}
        return GameCache(roomId,_metadata,_player_states,_properties,PlayerIconType.first,0,0, DiceType.Null, 0)

    @property
    def roomId(self) -> str: return self._roomId

    @property
    def metadata(self) -> PlayerMetadataSet: return self._metadata

    @property
    def player_states(self) -> list[PlayerType]: return self._player_states

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

    @diceCache.setter
    def diceCache(self, value: DiceType): self._dice_cache = value

    @doublesCount.setter
    def doublesCount(self, value: int): self._doubles_count = value

    @metadata.setter
    def metadata(self,value: PlayerMetadataSet): self._metadata = value

    @player_states.setter
    def player_states(self,value: list[PlayerType]): self._player_states = value

    @properties.setter
    def properties(self,value: dict[int,PropertyType]): self._properties = value

    @nowInTurn.setter
    def nowInTurn(self,value: PlayerIconType): self._nowInTurn = value

    @govIncome.setter
    def govIncome(self,value: int): self._govIncome = value
    
    @charityIncome.setter
    def charityIncome(self,value: int): self._charityIncome = value


    def copy(self) -> Self:
        return GameCache(self._roomId,self._metadata, self._player_states,self._properties,self._nowInTurn,self._govIncome,self._charityIncome, self._dice_cache, self._doubles_count)

    @property
    def gameState(self) -> GameStateType:
        output = GameStateType(
            roomId=copy.deepcopy(self._roomId),
            players=copy.deepcopy(self.player_states),
            properties=copy.deepcopy(self.properties),
            nowInTurn=self.nowInTurn,
            govIncome=self.govIncome,
            charityIncome=self.charityIncome,
            diceCache=self.diceCache,
            doublesCount=self.doublesCount)
        return output


    
    def updateGameState(self, io: SocketIO, refresh: bool = False, isPlayable: bool | None = None) -> None:
        state: GameStateType = self.gameState
        serialized = serializeGameState(state)
        if refresh:
            if isPlayable is None or not isPlayable:
                payload = { "refresh": "true" , "gameState": serialized, "nowInTurnEmail": self.nowInTurnEmail, "isPlayable": "false"}
            else:
                payload = { "refresh": "true" , "gameState": serialized, "nowInTurnEmail": self.nowInTurnEmail, "isPlayable": "true"}
        else:
            payload = { "refresh": "false" , "gameState": serialized, "nowInTurnEmail": self.nowInTurnEmail}
        io.emit("updateGameState",payload,to=self.roomId,include_self=True)
        with Client("room.sqlite") as db:
            db.set(f"{self.roomId}",self)

    def commitState(self, state: GameStateType, io: SocketIO):
        self.player_states = copy.deepcopy(state.players)
        self.properties = copy.deepcopy(state.properties)
        self.nowInTurn = state.nowInTurn
        self.govIncome = state.govIncome
        self.charityIncome = state.charityIncome
        self.diceCache = state.diceCache
        self.doublesCount = state.doublesCount

        copied = GameStateType(copy.deepcopy(self._roomId),copy.deepcopy(self.player_states),copy.deepcopy(self.properties),self.nowInTurn,self.govIncome,self.charityIncome, self.diceCache, self.doublesCount)
        self.updateGameState(io,False)

    @classmethod
    def load(cls, roomId: str) -> Self | None:
        with Client("room.sqlite") as db:
            if db.exists(f"{roomId}"):
                imported: GameCache = db.get(f"{roomId}")
                return imported
            else: return None
            



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
    DiceType.SixSix: (6, 6),
}