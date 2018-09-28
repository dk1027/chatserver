import asyncio
import json
import websockets

ACTIVE_USERS = dict()
CHANNELS = dict()  # channel-name: list(user-name)

# TODO: What happens when my chat partner doens't exist? went offline?
# TODO: input validation...


async def register(websocket):
    print('new connection')


async def unregister(this_user):
    try:
        ACTIVE_USERS.pop(this_user)
        print('connection closed')
        print(f"active users {ACTIVE_USERS.keys()}")
    except Exception as e:
        print(f"{this_user} doesn't exist in ACTIVE_USERS??")


def user_init(payload, websocket):
    """
    payload:
    {
        "user": "your-user-name",
        "channel": "team-channel"
    }
    """
    try:
        user = payload['user']
        ACTIVE_USERS[user] = websocket
        if payload['channel'] not in CHANNELS:
            CHANNELS[payload['channel']] = set()
        CHANNELS[payload['channel']].add(user)
    except Exception as e:
        print(f"user_init: malformed payload? {payload}")


async def broadcast_msg(msg):
    websockets = [ACTIVE_USERS[k] for k in ACTIVE_USERS.keys()]
    await asyncio.wait([ws.send(msg) for ws in websockets])


async def direct_msg(payload):
    """
    payload:
    {
        'target_user' :'other person username'
        'msg': 'str' # TODO: Impose msg limit?
    }
    """
    try:
        target_user = payload['target_user']
        msg = payload['msg']
        ws = ACTIVE_USERS[target_user]
        await asyncio.wait([ws.send(msg)])
    except Exception as e:
        print(str(e))
        print("payload", payload)
        print("ACTIVE_USERS", ACTIVE_USERS.keys())


async def send_msg(payload):
    """
    {
        "type": "channel|user"
        "target_channel" :'username or channel name'
        'msg': 'str' # TODO: Impose msg limit?
    }
    """
    type = payload['type']
    channel = payload['target_channel']
    msg = payload['msg']
    if type == 'channel':
        members = CHANNELS[channel]  # usernames .. not ws
        websockets = [ACTIVE_USERS[username] for username in ACTIVE_USERS.keys() if username in members]
        await asyncio.wait([ws.send(msg) for ws in websockets])
    else:
        # TODO: fix direct msg
        # check type == user
        # pick out the websocket for the user
        # send msg
        raise Exception("Not yet implemented")

async def hello(websocket, path):
    await register(websocket)
    try:
        need_init = True
        this_user = 'unknown'
        async for message in websocket:
            if need_init:
                # first message is always the initialize payload
                # e.g. {'user': 'your-user-name'}
                data = json.loads(message)
                print(data)
                user_init(data, websocket)
                this_user = data['user']
                print(f'this user: {this_user}')
                msg = f"new connection: active users {ACTIVE_USERS.keys()}, channels: {CHANNELS}"
                print(msg)
                await broadcast_msg(msg)
                need_init = False
            # from here on, assume its all chat messages
            print(message)
            await direct_msg(json.loads(message))
    finally:
        # REVISIT: why is there a stack trace when the client disconnects?
        # However server isn't exitting..... maybe there's a connection handler
        # I need to define?
        await unregister(this_user)

start_server = websockets.serve(hello, 'localhost', 8765)

asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()
