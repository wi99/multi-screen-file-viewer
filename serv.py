
# https://websockets.readthedocs.io/en/stable/intro.html#synchronization-example
# WS server example that synchronizes state across clients

import asyncio
import json
import logging
import websockets

logging.basicConfig()

STATE = {"x": 0, "y": 0}

USERS = set()


def state_event():
	return json.dumps({"type": "state", **STATE})


#def users_event():
#	return json.dumps({"type": "users", "count": len(USERS)})


async def notify_state():
	if USERS:  # asyncio.wait doesn't accept an empty list
		message = state_event()
		await asyncio.wait([user.send(message) for user in USERS])


#async def notify_users():
#	if USERS:  # asyncio.wait doesn't accept an empty list
#		message = users_event()
#		await asyncio.wait([user.send(message) for user in USERS])


async def register(websocket):
	USERS.add(websocket)
#	await notify_users()


async def unregister(websocket):
	USERS.remove(websocket)
#	await notify_users()


async def position_updater(websocket, path):
	# register(websocket) sends user_event() to websocket
	await register(websocket)
	try:
		await websocket.send(state_event())
		async for message in websocket:
			data = json.loads(message)
			STATE['x'] = data['x']
			STATE['y'] = data['y']
			await notify_state()
	finally:
		await unregister(websocket)


start_server = websockets.serve(position_updater, port=6789)

asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()
