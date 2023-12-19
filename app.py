from copy import deepcopy
from functools import cache
from math import floor
from time import sleep
import flask

import flask_socketio

import flask_cors

import json as JSON

from manager import *
from primitives import *
from cells import *
from chances import *
from utils import *

import random

import copy


class RoomCreationExceptionReason(Enum):
    already_exists = "already exists"
    failure = "failed"

class RoomCreationException(Exception):
    def __init__(self, reason: RoomCreationExceptionReason):
        super().__init__()
        self.reason: RoomCreationExceptionReason = reason


caches: dict[str, GameCache] = {}





app = flask.Flask(__name__)
flask_cors.CORS(app,origins=[
        "https://ku-obp.vercel.app",
        "https://ku-obp-gamma.vercel.app",
        "http://localhost:3000",
    ],allow_headers=[
        "Content-Type",
        "Authorization",
        "Access-Control-Allow-Origin"
    ],supports_credentials=True,
    methods=[
        "GET", "POST", "OPTIONS"
    ])


io = flask_socketio.SocketIO(app,
    cors_allowed_origins=[
        "https://ku-obp.vercel.app",
        "https://ku-obp-gamma.vercel.app",
        "http://localhost:3000",
    ],
    
    
)

main = flask.Blueprint('main', __name__)


def tryCreate():
    try:
        content = flask.request.get_json()
        roomId = content["roomId"]
        hostEmail = content["player1"]
        guest1 = content["player2"]
        guest2 = content["player3"]
        guest3 = content["player4"]
    except:
        raise RoomCreationException(reason=RoomCreationExceptionReason.failure)
    else:
        if roomId in caches.keys():
            raise RoomCreationException(reason=RoomCreationExceptionReason.already_exists)
        else:
            loaded = GameCache.load(roomId)
            if loaded is not None:
                caches[roomId] = copy.deepcopy(loaded)
                raise RoomCreationException(reason=RoomCreationExceptionReason.already_exists)
            else:
                caches[roomId] = GameCache.initialize(roomId,hostEmail,guest1,3,False,guest2,guest3)




@main.route("/")
def index():
    return "<div>Hello, World!</div>"


@main.route('/create', methods=["POST"])
def create():
    try:
        tryCreate()
    except RoomCreationException as e:
        response = flask.jsonify({"status": e.reason.value})
        response.status_code = 200
        return response
    else:
        response = flask.jsonify({"status": "succeeded"})
        response.status_code = 200
        return response
    finally:
        print("/crate call 호출됨")




@io.on("joinRoom")
def joinRoom(json):
    print(f"\n\n{json}\n\n")
    loaded = json
    roomId = str(loaded["roomId"])

    if roomId in caches.keys():
        flask_socketio.join_room(roomId)
        emit("joinSucceed", broadcast=False)
        cache = caches[roomId]
        cache.notifyLoad()
        print(f"join succeed to {roomId}")

    else:
        emit("joinFailed", {"msg": "invalid room"}, broadcast=False)
        print("joinFailed: invalid room")


def randomDice() -> tuple[Literal[1,2,3,4,5,6], Literal[1,2,3,4,5,6]]:
    base: list[Literal[1,2,3,4,5,6]] = [1,2,3,4,5,6]
    dice1 = random.choice(base)
    dice2 = random.choice(base)
    return (dice1, dice2)
    


def reportNormalTurnDIce(json):
    loaded = json
    roomId = str(loaded["roomId"])
    
    (dice1, dice2) = randomDice()
    
    caches[roomId].reportDices(dice1, dice2, io)
    caches[roomId].go((dice1+dice2),io)




def sellForDebt(json):
    loaded = json
    roomId = str(loaded["roomId"])
    targetLocation = int(loaded["targetLocation"])
    amount = int(loaded["amount"])
    
    cache = caches[roomId]
    cache.sellForDebt(targetLocation,amount,io)

def _nextTurn(roomId: str, jailbreak: bool = False):
    caches[roomId].prompt = CellPromptType.none
    caches[roomId].chanceCardDisplay = ""
    sleep(0.6)
    isdouble = caches[roomId].isDouble() and not jailbreak
    triggerEndGame = caches[roomId].tryNextTurn(isdouble, io)
    caches[roomId].commitGameState(None,io)
    io.emit("eraseQuirkOfFateStatus",to=roomId,include_self=True)
    if triggerEndGame:
        caches[roomId].endGame(io)

def lotto(judge: Callable[[Eisenstein], bool]) -> bool:
    a = round(random.gammavariate(3,2))
    b = round(random.gammavariate(3,2))
    x = Eisenstein(a,b)
    return judge(x)

def _calculateLottoRewards(roomId: str, final_result: int, doubles: bool):
    nowInTurn = caches[roomId].nowInTurn
    if final_result >= 3:
        _reward: int = 2000000
    elif final_result == 2:
        _reward: int = 1000000
    elif final_result == 1:
        _reward: int = 500000
    else:
        _reward: int = 0
    
    if doubles:
        reward = _reward * 2
    else:
        reward = _reward

    after = caches[roomId].playerStates[nowInTurn.value].cash + reward
    caches[roomId].playerStates[nowInTurn.value].cash = after

    caches[roomId].lottoSuccess = 0

def tryLotto(json):
    loaded = json
    roomId = str(loaded["roomId"])
    _usingDoubleLotto = str(loaded["usingDoubleLotto"])
    usingDoubleLotto = (_usingDoubleLotto == "true")
    flagDoubleLotto = caches[roomId].usingDoubleLotto or usingDoubleLotto
    caches[roomId].usingDoubleLotto = flagDoubleLotto

    nowInTurn = caches[roomId].nowInTurn
    beforeCash = caches[roomId].playerStates[nowInTurn.value].cash
    if beforeCash >= 200000:
        caches[roomId].playerStates[nowInTurn.value].cash = max(0,beforeCash - 200000)

        before = max(0,caches[roomId].lottoSuccess)
        judgement = lotto(Eisenstein.isPrime)
        if judgement:
            if (before >= 2) or (caches[roomId].playerStates[nowInTurn.value].cash < 200000):
                _calculateLottoRewards(roomId,3, caches[roomId].usingDoubleLotto)
                _nextTurn(roomId)
            else:
                caches[roomId].lottoSuccess = before + 1
                caches[roomId].commitGameState(None,io)
        else:
            _nextTurn(roomId)
    else:
        _nextTurn(roomId)
        

def purchase(json):
    loaded = json
    roomId = str(loaded["roomId"])
    amount = min(3,max(1,int(loaded["amount"])))
    nowInTurn = caches[roomId].nowInTurn
    cellId = (caches[roomId].playerStates[nowInTurn.value].location) % 54
    maxBuildable = PREDEFINED_CELLS[cellId].maxBuildable
    if maxBuildable == BuildableFlagType.NotBuildable:
        pass
    elif cellId in caches[roomId].properties.keys():
        before_count = caches[roomId].properties[cellId].count
        before_cash = caches[roomId].playerStates[nowInTurn.value].cash
        available_amount = min(amount, caches[roomId].playerStates[nowInTurn.value].cycles, maxBuildable.value - before_count)
        if (available_amount > 0) and (before_cash >= (300000 * available_amount)):
            (
                caches[roomId].properties[cellId].count,
                caches[roomId].playerStates[nowInTurn.value].cash
            ) = (
                before_count + available_amount,
                before_cash - (300000 * available_amount)
            )
        else:
            pass
    else:
        before_cash = caches[roomId].playerStates[nowInTurn.value].cash
        available_amount = min(amount, caches[roomId].playerStates[nowInTurn.value].cycles, maxBuildable.value)
        if (available_amount > 0) and (before_cash >= (300000 * available_amount)):
            (
                caches[roomId].properties[cellId].count,
                caches[roomId].playerStates[nowInTurn.value].cash
            ) = (
                available_amount,
                before_cash - (300000 * available_amount)
            )
        else:
            pass
    
    _nextTurn(roomId)

def skip(json):
    loaded = json
    roomId = str(loaded["roomId"])
    
    _nextTurn(roomId)


def tryJailExitByDice(json):
    loaded = json
    roomId = str(loaded["roomId"])

    (dice1, dice2) = randomDice()
    
    caches[roomId].reportDices(dice1, dice2, io)

    dices = DICE_REVERSE_LOOKUP[(dice1, dice2)]

    caches[roomId].tryJailExit(dices)
    
    _nextTurn(roomId)

def jailExitThanksToLawyer(json):
    loaded = json
    roomId = str(loaded["roomId"])

    caches[roomId].tryJailExit(DiceType.Null,True)
    
    _nextTurn(roomId)


def jailExitByCash(json):
    loaded = json
    roomId = str(loaded["roomId"])

    caches[roomId].tryJailExit(DiceType.Null,False)
    
    _nextTurn(roomId)


def trafficJam(json):
    loaded = json
    roomId = str(loaded["roomId"])
    target = int(loaded["target"]) % 54

    if target in caches[roomId].properties.keys() and (PREDEFINED_CELLS[target].maxBuildable != BuildableFlagType.NotBuildable) and caches[roomId].properties[target].ownerIcon != caches[roomId].nowInTurn:
        before = caches[roomId].properties[target].count
        caches[roomId].properties[target].count = max(0,before - 1)
        caches[roomId]._garbageCollection()
        
        _nextTurn(roomId)


def trade(json):
    loaded = json
    roomId = str(loaded["roomId"])
    toGive = int(loaded["toGive"]) % 54
    toGet = int(loaded["toGet"]) % 54

    nowInTurn = caches[roomId].nowInTurn

    isMine = toGive in caches[roomId].properties.keys() and (PREDEFINED_CELLS[toGive].maxBuildable != BuildableFlagType.NotBuildable) and (caches[roomId].properties[toGive].ownerIcon == nowInTurn)
    isOthers = toGet in caches[roomId].properties.keys() and (PREDEFINED_CELLS[toGet].maxBuildable != BuildableFlagType.NotBuildable) and (caches[roomId].properties[toGet].ownerIcon != nowInTurn)

    if isMine and isOthers:
        (tmp1, tmp2) = (caches[roomId].properties[toGive].ownerIcon.value, caches[roomId].properties[toGet].ownerIcon.value)
        (caches[roomId].properties[toGive].ownerIcon, caches[roomId].properties[toGet].ownerIcon) = (PlayerIconType(tmp2), PlayerIconType(tmp1))
        
        _nextTurn(roomId)

def extinction(json):
    loaded = json
    roomId = str(loaded["roomId"])
    targetGroup = int(loaded["targetGroup"])

    groupCellIds = dict(filter(lambda cell: cell[1].group_factor == targetGroup,PREDEFINED_CELLS.items()))
    searchResult = set(copy.deepcopy(groupCellIds.keys())).intersection(caches[roomId].properties.keys())

    copied = copy.deepcopy(caches[roomId].properties)

    flag: bool = False
    for cellId in searchResult:
        before = copied[cellId].count
        copied[cellId].count = max(0,before - 1)
        flag = True
    else:
        if flag:
            caches[roomId].properties = copy.deepcopy(copied)
            
            _nextTurn(roomId)

def quickMove(json):
    loaded = json
    roomId = str(loaded["roomId"])
    dest = int(loaded["dest"])

    nowInTurn = caches[roomId].nowInTurn
    if dest in PREDEFINED_CELLS.keys():
        if dest == caches[roomId].playerStates[nowInTurn.value].location:
            amount = 54
        else:
            amount = dest - caches[roomId].playerStates[nowInTurn.value].location
        turn_finished = caches[roomId].go(amount, io)
        if turn_finished:
            _nextTurn(roomId)


def greenNewDeal(json):
    loaded = json
    roomId = str(loaded["roomId"])
    target = int(loaded["target"])

    nowInTurn = caches[roomId].nowInTurn

    if target in caches[roomId].properties.keys():
        before = caches[roomId].properties[target].count
        maximum = PREDEFINED_CELLS[target].maxBuildable.value
        if (caches[roomId].properties[target].ownerIcon == nowInTurn) and (before < PREDEFINED_CELLS[target].maxBuildable.value):
            caches[roomId].properties[target].count = min(before + 1, maximum)
            _nextTurn(roomId)
            

def quirkOfFate(json):
    loaded = json
    roomId = str(loaded["roomId"])

    (dice1, dice2) = randomDice()
    io.emit("showQuirkOfFateStatus", (int(dice1), int(dice2)))

    l = len(caches[roomId].playerStates)

    nowInTurn = caches[roomId].nowInTurn

    if l == 2:
        target = (caches[roomId].nowInTurn.value + dice1 + dice2) % 2
    elif l == 3:
        target = (caches[roomId].nowInTurn.value + dice1 + dice2) % 3
    elif l == 4:
        target = (caches[roomId].nowInTurn.value + dice1 + dice2) % 4
    else:
        return
    
    if target != nowInTurn.value:
        copied = copy.deepcopy(caches[roomId].properties)
        myPropertyIds = set(map(lambda p: p[0],filter(lambda p: p[1].ownerIcon.value == nowInTurn.value,copied.items())))
        targetsPropertyIds = set(map(lambda p: p[0],filter(lambda p: p[1].ownerIcon.value == target,copied.items())))
        targetIcon = getIcon(target)
        for myPropertyId in myPropertyIds:
            caches[roomId].properties[myPropertyId].ownerIcon = targetIcon
        
        for targetsPropertyId in targetsPropertyIds:
            caches[roomId].properties[targetsPropertyId].ownerIcon = nowInTurn

        (
            caches[roomId].playerStates[nowInTurn.value].cash,
            caches[roomId].playerStates[target].cash
        ) = (
            caches[roomId].playerStates[target].cash,
            caches[roomId].playerStates[nowInTurn.value].cash
        )

        _nextTurn(roomId)


    

def pickChance(json):
    loaded = json
    roomId = str(loaded["roomId"])
    caches[roomId].prompt = CellPromptType.none
    caches[roomId].commitGameState(None,io)
    caches[roomId].getChance(io)






@io.event
def connect():
    io.on_event("reportNormalTurnDice", reportNormalTurnDIce)    
    io.on_event("sellForDebt", sellForDebt)

    io.on_event("tryLotto", tryLotto)
    io.on_event("tryJailExitByDice", tryJailExitByDice)
    io.on_event("jailExitThanksToLawyer", jailExitThanksToLawyer)
    io.on_event("jailExitByCash", jailExitByCash)
    io.on_event("trafficJam", trafficJam)
    io.on_event("trade", trade)
    io.on_event("extinction", extinction)
    io.on_event("quickMove", quickMove)
    io.on_event("greenNewDeal", greenNewDeal)
    io.on_event("quirkOfFate", quirkOfFate)
    io.on_event("pickChance", pickChance)




app.register_blueprint(main)



if __name__ == "__main__":
    io.run(app)