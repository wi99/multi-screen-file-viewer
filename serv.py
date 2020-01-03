
# https://websockets.readthedocs.io/en/stable/intro.html#synchronization-example
# WS server example that synchronizes state across clients

import asyncio
import json
import logging
import websockets

#logging.basicConfig()
import sys
logging.basicConfig(stream=sys.stdout, level=logging.INFO)

POSITION = {"x": 0, "y": 0}

USERS = set() # aka connected

windowSizes = {} # key: websocket, value: (l,w)
offsets = {} # key: websocket, value: x,y. values are 0 or negative

def pos_event(ws):
	return json.dumps(
		{"type": "pos",
		'x': POSITION['x'] + offsets[ws][0],
		'y': POSITION['y'] + offsets[ws][1]}
	)


#def users_event():
#	return json.dumps({"type": "users", "count": len(USERS)})


async def notify_pos():
	if USERS:  # asyncio.wait doesn't accept an empty list
		await asyncio.wait([user.send(pos_event(user)) for user in USERS])


#async def notify_users():
#	if USERS:  # asyncio.wait doesn't accept an empty list
#		message = users_event()
#		await asyncio.wait([user.send(message) for user in USERS])


async def register(websocket):
	USERS.add(websocket)
	# logic for how to arrange the displays
	if len(offsets) == 0:
		offsets[websocket] = [0,0]
	else: #right now just putting things to the right of it
		x = y = 0
		for k,v in windowSizes.items(): # TODO: i think should be max(offset)+windowSize[thing], but maybe not because this isn't causing problems
			x -= v[0]
			#y += v[1]
		offsets[websocket] = [x,y]

	print("Offsets: ", offsets)
#	await notify_users()
#	logging.info("ws connected")


async def unregister(websocket):
	USERS.remove(websocket)
	w,h = windowSizes.pop(websocket, (0,0))

	# rearrange displays
	x,y = offsets.pop(websocket, (0,0))
	for user in USERS: # affected offsets are those to the right aka more negative
		if offsets[user][0] < x:
			offsets[user][0] += w

	#print("Offsets: ", offsets)
	if not USERS:
		POSITION['x'] = POSITION['y'] = 0 # TODO: if something long like pdf only x goes to zero but y stays the same
	await notify_pos()

async def position_updater(websocket, path):
	# register(websocket) sends user_event() to websocket
	await register(websocket)
	try:
		#await websocket.send(pos_event(websocket)) # don't need this anymore because JS sends onconnect
		async for message in websocket:
			data = json.loads(message)
			if data['type'] == 'pos':
				POSITION['x'] = data['x'] - offsets[websocket][0]
				POSITION['y'] = data['y'] - offsets[websocket][1] # currently offset y is zero for all
			elif data['type'] == 'dim':
#				if websocket in windowSizes:
#					delta_x = data['w'] - windowSizes[websocket][0]
#					#delta_y = data['h'] - windowSizes[websocket][1]
#					for user in USERS: # TODO: fix this. subsequent windows are not going as fast as the window is resizing, causing overlap
#						if offsets[user][0] < windowSizes[websocket][0]:
#							offsets[user][0] -= delta_x
				windowSizes[websocket] = data['w'], data['h']
				logging.info("window size: %sx%s",  data['w'], data['h'])

			else:
				logging.error("unsupported event: {}", data)
			await notify_pos()
	finally:
		await unregister(websocket)


start_server = websockets.serve(position_updater, port=6789)

asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()
