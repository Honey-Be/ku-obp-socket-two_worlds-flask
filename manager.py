from kvsqlite.sync import Client
import flask

import flask_socketio
from primitives import *

from random import shuffle

import copy
from typing import Any, Callable
from cells import PREDEFINED_CELLS

from utils import *

from collections.abc import Sequence

def distributeBasicIncome(state: GameStateType) -> GameStateType:
    if len(state.playerStates) < 2:
        return state
    else:
        new_state = copy.deepcopy(state)
        players_count = max(min(len(new_state.playerStates),4), 2)
        per_each = (new_state.govIncome) // players_count
        transaction = PaymentTransaction.distribute(per_each, players_count)
        _govIncome = new_state.govIncome - (per_each * players_count)
        tmp = GameStateType(new_state.roomId,new_state.playerStates,new_state.properties,new_state.nowInTurn,_govIncome,new_state.charityIncome, new_state.diceCache, new_state.doublesCount, state.remainingCatastropheTurns, state.remainingPandemicTurns)
        output = transaction.toAppliedState(tmp)
        return output
    
def _captureForImprisonment(player: PlayerType, player_icon: PlayerIconType) -> PlayerType:
    if player.icon == player_icon:
        return PlayerType(player.icon,player.location,player.displayLocation,player.cash,player.cycles,player.university,player.tickets,3)
    else:
        return player
    
def checkRemainingJailTurns(player: PlayerType) -> tuple[PlayerType, bool]:
    if player.remainingJailTurns > 1:
        return (PlayerType(player.icon,player.location,player.displayLocation,player.cash,player.cycles,player.university,player.tickets,player.remainingJailTurns - 1), False)
    else:
        return (PlayerType(player.icon,player.location,player.displayLocation,player.cash,player.cycles,player.university,player.tickets,0), True)


def imprisonment(state: GameStateType, player_icon: PlayerIconType) -> GameStateType:
    new_players = map(lambda p: _captureForImprisonment(p,player_icon),copy.deepcopy(state.playerStates))
    new_state = GameStateType(state.roomId,list(new_players),copy.deepcopy(state.properties),state.nowInTurn,state.govIncome,state.charityIncome, state.diceCache, state.doublesCount, state.remainingCatastropheTurns, state.remainingPandemicTurns)
    return state

def upgradeAtUniv(player: PlayerType, player_icon: PlayerIconType) -> PlayerType:
    if player.university == UniversityStateType.graduated:
        return player
    elif player.icon == player_icon:
        if player.university == UniversityStateType.notYet:
            new_player = PlayerType(player.icon,player.location,player.displayLocation,player.cash,player.cycles,UniversityStateType.undergraduate,player.tickets,player.remainingJailTurns)
        else:
            new_player = PlayerType(player.icon,player.location,player.displayLocation,player.cash,player.cycles,UniversityStateType.graduated,player.tickets,player.remainingJailTurns)
        return new_player
    else:
        return player


def universityAction(state: GameStateType, player_icon: PlayerIconType) -> GameStateType:
    new_players = map(lambda player: upgradeAtUniv(player,player_icon),copy.deepcopy(state.playerStates))
    return GameStateType(state.roomId,list(new_players),copy.deepcopy(state.properties),state.nowInTurn,state.govIncome,state.charityIncome, state.diceCache, state.doublesCount, state.remainingCatastropheTurns, state.remainingPandemicTurns)


def setDisplayLocation(player: PlayerType, displayLocation: int) -> PlayerType:
    return PlayerType(player.icon,player.location,displayLocation % 54,player.cash,player.cycles,player.university,player.tickets,player.remainingJailTurns)

def setLocation(player: PlayerType, location: int) -> PlayerType:
    return PlayerType(player.icon,location,player.displayLocation % 54,player.cash,player.cycles,player.university,player.tickets,player.remainingJailTurns)



def moveForward(state: GameStateType, player_icon: PlayerIconType, amount: int, callback: Callable[[GameStateType], None]) -> tuple[GameStateType, Sequence[AbstractPaymentType]]:
    tmp = copy.deepcopy(state)
    l: Sequence[AbstractPaymentType] = []
    players_count = len(state.playerStates)
    for i in range(players_count):
        if tmp.playerStates[i].icon == player_icon:
            src = tmp.playerStates[i].location
            for n in range(1, amount + 1):
                tmp.playerStates[i] = setDisplayLocation(tmp.playerStates[i], src + n)
                if(PREDEFINED_CELLS[tmp.playerStates[i].displayLocation].hasEffectWhenPassing):
                    tmp2 = PREDEFINED_CELLS[tmp.playerStates[i].displayLocation].passing(tmp,player_icon)
                    tmp = tmp2
                callback(tmp)
            new_location = (src + amount) % 54
            tmp.playerStates[i] = setLocation(tmp.playerStates[i],new_location)
            (tmp, l) = PREDEFINED_CELLS[new_location].arrived(tmp,player_icon)
            break;
        else: continue;
    return (tmp, l)


def moveBackward(state: GameStateType, player_icon: PlayerIconType, amount: int, callback: Callable[[GameStateType], None]) -> tuple[GameStateType, Sequence[AbstractPaymentType]]:
    tmp = copy.deepcopy(state)
    l: Sequence[AbstractPaymentType] = []
    players_count = len(state.playerStates)
    for i in range(players_count):
        if tmp.playerStates[i].icon == player_icon:
            src = tmp.playerStates[i].location
            for n in range(1, amount + 1):
                tmp.playerStates[i] = setDisplayLocation(tmp.playerStates[i], src - n)
                if(PREDEFINED_CELLS[tmp.playerStates[i].displayLocation].hasEffectWhenPassing):
                    tmp2 = PREDEFINED_CELLS[tmp.playerStates[i].displayLocation].passing(tmp,player_icon)
                    tmp = tmp2
                callback(tmp)
            new_location = (src - amount) % 54
            tmp.playerStates[i] = setLocation(tmp.playerStates[i],new_location)
            (tmp, l) = PREDEFINED_CELLS[new_location].arrived(tmp,player_icon)
            break;
        else: continue;
    callback(tmp)
    return (tmp, l)





def createRoom(roomId: str, cache: GameCache) -> None:
    with Client("room.sqlite") as db:
        db.set(f"{roomId}", cache)