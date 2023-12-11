from functools import cache
import flask

import flask_socketio

import flask_cors

import json as JSON

from manager import *
from primitives import *
from cells import *
from chances import *
from utils import *


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
        "http://localhost:3000",
        "https://ku-obp.vercel.app",
        "https://ku-obp-gamma.vercel.app"
    ],allow_headers=[
        "Content-Type",
        "Authorization",
        "Access-Control-Allow-Origin"
    ],supports_credentials=True,
    methods=[
        "GET", "POST", "OPTIONS"
    ])


io = flask_socketio.SocketIO(
    cors_allowed_origins=[
        "http://localhost:3000",
        "https://ku-obp.vercel.app",
        "https://ku-obp-gamma.vercel.app"
    ],
)


io.init_app(app)

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
        

def joinRoom(json):
    loaded = JSON.loads(json)
    playerEmail = loaded["playerEmail"]
    roomId = loaded["roomId"]

    if roomId in caches.keys():
        flask_socketio.join_room(roomId)
        io.emit("joinSucceed")
        cache = caches[roomId]
        state: GameStateType = cache.gameState
        serialized = serializeGameState(state)
        isPlayable = "true" if cache.metadata.has_emails(playerEmail) else "false"
        payload = { "refresh": "true" , "gameState": serialized, "nowInTurnEmail": cache.nowInTurnEmail, "isPlayable": isPlayable}
        io.emit("updateGameState",payload)
        io.emit("updateDoublesCount",cache.doublesCount)
        dices = DICE_LOOKUP[cache.diceCache]
        io.emit("showDIces",{ "dice1": dices[0], "dice2": dices[1]})

    else:
        io.emit("joinFailed", {"msg": "invalid room"})



@io.on("connect")
def connect(sid, environ):
    print(f"{sid} is connected.")
    io.on_event("joinRoom",joinRoom)    


if __name__ == "__main__":
    io.run(app, host="0.0.0.0", port=11000, use_reloader=True, log_output=True,allow_unsafe_werkzeug=True)