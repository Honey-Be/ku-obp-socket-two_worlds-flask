from kvsqlite.sync import Client
from primitives import *

from random import shuffle

import copy
from typing import Callable
from cells import CELLS


def distributeBasicIncome(state: GameStateType) -> GameStateType:
    if len(state.players) < 2:
        return state
    else:
        new_state = copy.deepcopy(state)
        players_count = min(len(new_state.players),4)
        per_each = (new_state.govIncome) // players_count
        transaction = PaymentTransaction.distribute(per_each, players_count)
        new_state.govIncome = new_state.govIncome - (per_each * players_count)
        output = transaction.toAppliedState(new_state)
        return output
    
def _captureForImprisonment(player: PlayerType, player_icon: PlayerIconType) -> PlayerType:
    if player.icon == player_icon:
        player.remainingJailTurns = 3
        return player
    else:
        return player
    
def checkRemainingJailTurns(player: PlayerType) -> [PlayerType, bool]:
    if player.remainingJailTurns > 1:
        player.remainingJailTurns = player.remainingJailTurns - 1
        return [player, False]
    else:
        player.remainingJailTurns = 0
        return [player, True]


def imprisonment(state: GameStateType, player_icon: PlayerIconType) -> GameStateType:
    new_players = map(lambda p: _captureForImprisonment(p,player_icon),copy.deepcopy(state.players))
    state.players = list(new_players)
    return state

def upgradeAtUniv(player: PlayerType, player_icon: PlayerIconType) -> PlayerType:
    if player.university == UniversityStateType.graduated:
        return player
    elif player.icon == player_icon:
        new_player = copy.deepcopy(player)
        if player.university == UniversityStateType.notYet:
            new_player.university = UniversityStateType.undergraduate
        else:
            new_player.university = UniversityStateType.graduated
        return new_player


def universityAction(state: GameStateType, player_icon: PlayerIconType) -> GameStateType:
    new_players = map(upgradeAtUniv,copy.deepcopy(state.players))
    state.players = new_players
    return state


def setDisplayLocation(player: PlayerType, location: int) -> PlayerType:
    player.displayLocation = location % 54
    return player



def moveForward(state: GameStateType, player_icon: PlayerIconType, amount: int, callback: Callable[[GameStateType], None]) -> tuple[GameStateType, list[AbstractPaymentType]]:
    tmp = copy.deepcopy(state)
    l: list[AbstractPaymentType] = []
    players_count = len(state.players)
    for i in range(players_count):
        if tmp.players[i].icon == player_icon:
            src = tmp.players[i].location
            for n in range(1, amount + 1):
                tmp.players[i] = setDisplayLocation(tmp.players[i], src + n)
                if(CELLS[tmp.players[i].displayLocation].hasEffectWhenPassing):
                    tmp2 = CELLS[tmp.players[i].displayLocation].passing(tmp,player_icon)
                    tmp = tmp2
                callback(tmp)
            new_location = (src + amount) % 54
            tmp.players[i].location = new_location
            [tmp3, l3] = CELLS[new_location].arrived(tmp,player_icon)
            [tmp, l] = [tmp3, l3]
            break;
        else: continue;
    return [tmp, l]


def moveBackward(state: GameStateType, player_icon: PlayerIconType, amount: int, callback: Callable[[GameStateType], None]) -> tuple[GameStateType, list[AbstractPaymentType]]:
    tmp = copy.deepcopy(state)
    l: list[AbstractPaymentType] = []
    players_count = len(state.players)
    for i in range(players_count):
        if tmp.players[i].icon == player_icon:
            src = tmp.players[i].location
            for n in range(1, amount + 1):
                tmp.players[i] = setDisplayLocation(tmp.players[i], src - n)
                if(CELLS[tmp.players[i].displayLocation].hasEffectWhenPassing):
                    tmp2 = CELLS[tmp.players[i].displayLocation].passing(tmp,player_icon)
                    tmp = tmp2
                callback(tmp)
            new_location = (src - amount) % 54
            tmp.players[i].location = new_location
            [tmp3, l3] = CELLS[new_location].arrived(tmp,player_icon)
            [tmp, l] = [tmp3, l3]
            break;
        else: continue;
    callback(tmp)
    return [tmp, l]


def warp(state: GameStateType, player_icon: PlayerIconType, dest: int, callback: Callable[[GameStateType], None], do_arrived: bool = True) -> tuple[GameStateType, list[AbstractPaymentType]]:
    players_count = len(state.players)
    tmp = copy.deepcopy(state)
    l: list[AbstractPaymentType] = []
    for i in range(players_count):
        if tmp.players[i].icon == player_icon:
            tmp.players[i].displayLocation = tmp.players[i].location = dest % 54
            if do_arrived:
                tmp2 = CELLS[dest % 54].arrived(tmp, player_icon)
                [tmp, l] = tmp2    
            break
        else: continue
    callback(tmp)
    return [tmp, l]


