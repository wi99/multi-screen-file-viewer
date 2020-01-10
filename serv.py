

import asyncio
import json
import logging
import websockets
import time

logging.basicConfig()
#import sys
#logging.basicConfig(stream=sys.stdout, level=logging.INFO)

POSITION = {"x": 0, "y": 0}

SCREENS = set() # aka connected

windowSizes = {} # key: websocket, value: (l,w)
offsets = {} # key: websocket, value: x,y. values are 0 or negative

totalWidth = 0
totalHeight = 0
maxWidth = 0
maxHeight = 0

# TODO: make these persist after exiting program.
class VideoState:
	saveTime = time.time()
	playbackTime = 0
	paused = True

def pos_event(ws):
	return json.dumps(
		{"type": "pos",
		'x': POSITION['x'] + offsets[ws][0],
		'y': POSITION['y'] + offsets[ws][1]}
	)

def dim_event():
	## Fit Width
	#return json.dumps({'type': 'dim', 'w': str(totalWidth) + 'px', 'h': 'auto'})
	## Fit Height
	#return json.dumps({'type': 'dim', 'w': 'auto', 'h': str(totalHeight) + 'px'})
	## Fit Page
	return json.dumps({'type': 'dim', 'w': str(totalWidth) + 'px', 'h': str(maxHeight) + 'px'})

def action_event(action):
	return json.dumps({'type': 'ctrl', 'action': action})


async def notify_pos():
	if SCREENS:  # asyncio.wait doesn't accept an empty list
		await asyncio.wait([screen.send(pos_event(screen)) for screen in SCREENS])

async def notify_dim():
	if SCREENS:
		message = dim_event()
		await asyncio.wait([screen.send(message) for screen in SCREENS])

async def notify_relay(data):
	if SCREENS:
		message = json.dumps(data)
		await asyncio.wait([screen.send(message) for screen in SCREENS])


async def register(websocket):
	SCREENS.add(websocket)
	# logic for how to arrange the displays
	if not offsets:
		offsets[websocket] = [0,0]
	else: #right now just extending displays to the right
		global totalWidth
		offsets[websocket] = [-totalWidth, 0]

	windowSizes[websocket] = (0,0)
	
	if not VideoState.paused:
		VideoState.playbackTime += time.time() - VideoState.saveTime
	action = 'pause' if VideoState.paused else 'play'
	await websocket.send(json.dumps({"type": "ctrl", "action": action, "time": VideoState.playbackTime}))


async def unregister(websocket):
	SCREENS.remove(websocket)
	w,h = windowSizes.pop(websocket, (0,0))

	global totalWidth, totalHeight
	totalWidth -= w
	totalHeight -= h

	# rearrange displays
	x,y = offsets.pop(websocket, (0,0))
	for screen in SCREENS: # affected offsets are those to the right aka more negative
		if offsets[screen][0] < x:
			offsets[screen][0] += w

	# reset and revert values
	if not SCREENS:
		# general
		POSITION['x'] = POSITION['y'] = 0 # TODO: if something long like pdf only x goes to zero but y stays the same
	else:
		global maxWidth, maxHeight
		maxWidth = max(windowSizes.values())[0]
		maxHeight = max(windowSizes.values(), key=lambda x:x[1])[1]
	
	# save values
	## video
	if not VideoState.paused:
		VideoState.playbackTime += time.time() - VideoState.saveTime # will be inaccurate if the last client disconnects the wrong way.
	await notify_pos()
	await notify_dim()

async def position_updater(websocket, path):
	await register(websocket)
	try:
		async for message in websocket:
			data = json.loads(message)
			if data['type'] == 'pos':
				POSITION['x'] = data['x'] - offsets[websocket][0]
				POSITION['y'] = data['y'] - offsets[websocket][1]
				await notify_pos()

			elif data['type'] == 'dim':
				global totalWidth, totalHeight, maxWidth, maxHeight
				delta_x = data['w'] - windowSizes[websocket][0]
				delta_y = data['h'] - windowSizes[websocket][1]
				totalWidth += delta_x
				totalHeight += delta_y
				if maxWidth < data['w']:
					maxWidth = data['w']
				if maxHeight < data['h']:
					maxHeight = data['h']
				for screen in SCREENS:
					if offsets[screen][0] < offsets[websocket][0]:
						offsets[screen][0] -= delta_x
				windowSizes[websocket] = (data['w'], data['h'])
				logging.info("window size: %sx%s",  data['w'], data['h'])
				await notify_dim()
				await notify_pos()

			elif data['type'] == 'ctrl':
				await notify_relay(data)
				VideoState.playbackTime = data['time']
				VideoState.saveTime = time.time()
				if data['action'] == 'pause':
					VideoState.paused = True
				else: # data['action'] == 'play'
					VideoState.paused = False
			else:
				logging.error("unsupported event: {}", data)

	finally:
		await unregister(websocket)


start_server = websockets.serve(position_updater, port=6789)

asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()
