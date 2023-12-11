from cells import *
from primitives import *
from manager import *
import random

from typing import Callable

class ChanceCardType:
    def __init__(self, chance_id: str, description: str, display_name: str, action: Callable[[GameStateType, Literal[0,1,2,3]], GameStateType], is_moving: bool):
        self._chance_id: str = chance_id
        self._description: str = description
        self._display_name: str = display_name
        self._action: Callable[[GameStateType, Literal[0,1,2,3]], GameStateType] = action
        self._is_moving: bool = is_moving

    @property
    def chanceId(self) -> str:
        return self._chance_id
    
    @property
    def description(self) -> str:
        return self._description
    @property
    def display_name(self) -> str:
        return self._display_name
    
    def action(self, state: GameStateType, playerIcon: PlayerIconType) -> GameStateType:
        return self._action(state,playerIcon.value)
    
    @property
    def is_moving(self) -> bool:
        return self._is_moving


CHANCE_CARDS: list[ChanceCardType] = [

]