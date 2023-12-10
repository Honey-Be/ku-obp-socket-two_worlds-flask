import socketio

io = socketio.Server(
    cors_allowed_origins=[
        "http://localhost:3000",
        "https://ku-obp.vercel.app",
        "https://ku-obp-gamma.vercel.app"
    ]
)

@io.event
def connect(sid, environ):
    print(f"{sid} is connected")

@io.on("joinRoom")
def joinRoom(sid, data):
    io.save_session(sid, data)
    io.enter_room(sid,data["roomId"])