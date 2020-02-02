from flask import Flask
from flask_sockets import Sockets
import geventwebsocket
import asyncio, time, json

app = Flask(__name__)
sockets = Sockets(app)

POSITION = {"x": 0, "y": 0}

SCREENS = set() # aka connected

windowSizes = {} # key: websocket, value: (l,w)
offsets = {} # key: websocket, value: x,y. values are 0 or negative

class Dimensions:
	totalWidth = 0
	totalHeight = 0
	maxWidth = 0
	maxHeight = 0


# TODO: make these persist after exiting program.
class VideoState:
	saveTime = time.time()
	playbackTime = 0
	paused = True

class PDFState:
	page = 1

class args: # TODO: gui this
	filetype = 'pdf' # 'image', 'pdf', or 'video'
	fit = 'width' # 'width', 'height', or 'page'

def pos_event(ws):
	return json.dumps(
		{"type": "pos",
		'x': POSITION['x'] + offsets[ws][0],
		'y': POSITION['y'] + offsets[ws][1]}
	)

def dim_event():
	if args.fit == 'width': ## Fit Width
		return json.dumps({'type': 'dim', 'w': str(Dimensions.totalWidth) + 'px', 'h': 'auto'})
	elif args.fit == 'height': ## Fit Height
		return json.dumps({'type': 'dim', 'w': 'auto', 'h': str(Dimensions.totalHeight) + 'px'})
	else: ## Fit Page
		return json.dumps({'type': 'dim', 'w': str(Dimensions.totalWidth) + 'px', 'h': str(Dimensions.maxHeight) + 'px'})

def action_event(action):
	return json.dumps({'type': 'ctrl', 'action': action})

def notify_pos():
	for screen in SCREENS:
		screen.send(pos_event(screen))

def notify_dim():
	message = dim_event()
	for s in SCREENS:
		s.send(message)


def notify_relay(data):
	message = json.dumps(data)
	for s in SCREENS:
		s.send(message)

def register(websocket):
	SCREENS.add(websocket)
	# logic for how to arrange the displays
	if not offsets:
		offsets[websocket] = [0,0]
	else: # extending displays to the right for fitwidth and fitpage
		if args.fit != 'height':
			offsets[websocket] = [-Dimensions.totalWidth, 0]
		else:
			offsets[websocket] = [0, -Dimensions.totalHeight]


	windowSizes[websocket] = (0,0)
	
	if args.filetype == 'video':
		if not VideoState.paused:
			VideoState.playbackTime += time.time() - VideoState.saveTime
		action = 'pause' if VideoState.paused else 'play'
		websocket.send(json.dumps({"type": "ctrl", "action": action, "time": VideoState.playbackTime}))
	if args.filetype == 'pdf':
		websocket.send(json.dumps({'value': str(PDFState.page), 'type': "ctrl", 'action': "pagenumberchanged"}))


def unregister(websocket):
	SCREENS.remove(websocket)
	w,h = windowSizes.pop(websocket, (0,0))

	Dimensions.totalWidth -= w
	Dimensions.totalHeight -= h

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
		Dimensions.maxWidth = max(windowSizes.values())[0]
		Dimensions.maxHeight = max(windowSizes.values(), key=lambda x:x[1])[1]
	
	# save values
	if args.filetype == 'video':
		if not VideoState.paused:
			VideoState.playbackTime += time.time() - VideoState.saveTime # will be inaccurate if the last client disconnects the wrong way.
	notify_pos()
	notify_dim()


@sockets.route('/sync')
def sync_socket(ws):
	register(ws)
	print(len(SCREENS))
	try:
		while not ws.closed:
			message = ws.receive()
			print(message)
			data = json.loads(message)
			if data['type'] == 'pos':
				POSITION['x'] = data['x'] - offsets[ws][0]
				POSITION['y'] = data['y'] - offsets[ws][1]
				notify_pos()

			elif data['type'] == 'dim':
				delta_x = data['w'] - windowSizes[ws][0]
				delta_y = data['h'] - windowSizes[ws][1]
				Dimensions.totalWidth += delta_x
				Dimensions.totalHeight += delta_y
				if Dimensions.maxWidth < data['w']:
					Dimensions.maxWidth = data['w']
				if Dimensions.maxHeight < data['h']:
					Dimensions.maxHeight = data['h']
				for screen in SCREENS:
					if offsets[screen][0] < offsets[ws][0]:
						offsets[screen][0] -= delta_x
				windowSizes[ws] = (data['w'], data['h'])
				print("window size: " + str(data['w']) + "x" + str(data['h']))
				notify_dim()
				notify_pos()

			elif data['type'] == 'ctrl':
				data['filetype'] = args.filetype
				notify_relay(data)
				if args.filetype == 'video':
					VideoState.playbackTime = data['time']
					VideoState.saveTime = time.time()
					if data['action'] == 'pause':
						VideoState.paused = True
					else: # data['action'] == 'play'
						VideoState.paused = False
				if args.filetype == 'pdf':
					if data['action'] == 'nextpage':
						PDFState.page += 1
					elif data['action'] == 'previouspage':
						PDFState.page -= 1
					elif data['action'] == 'pagenumberchanged':
						PDFState.page = int(data['value'])
	except geventwebsocket.exceptions.WebSocketError:
		print('client disconnected')
		pass
	finally:
		unregister(ws)

@app.route('/')
def index():
	print(args.filetype)
	if args.filetype == 'image':
		return app.send_static_file('image.html')
	if args.filetype == 'pdf':
		return app.send_static_file('pdf.html')
	# if args.filetype == 'video':
	return app.send_static_file('video.html')

if __name__ == "__main__":
	from gevent import pywsgi
	from geventwebsocket.handler import WebSocketHandler
	server = pywsgi.WSGIServer(('', 5000), app, handler_class=WebSocketHandler)
	server.serve_forever()
