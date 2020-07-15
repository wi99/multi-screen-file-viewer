from flask import Flask
from flask_sockets import Sockets
from flask import request
import geventwebsocket
import asyncio, time, json
import logging

app = Flask(__name__)
sockets = Sockets(app)

currentController = None # only 1 controller client at a time
SCREENS = [] # aka connected clients
POSITION = {"x": 0, "y": 0}
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

class args:
	filetype = 'pdf' # 'image', 'pdf', or 'video'
	fit = 'width' # 'width', 'height', or 'page' # default placement to 0,0 option is another possibility
	# TODO: seperate default placement and default zoom variables, because fit does both. defaultZoomFit, defaultAddScreen

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
	
		if currentController:
			currentController.send(json.dumps({'type': 'pos', 'i': SCREENS.index(s), 'x': offsets[s][0], 'y': offsets[s][1], 'w': windowSizes[s][0], 'h': windowSizes[s][1]}))

def notify_relay(data):
	message = json.dumps(data)
	for s in SCREENS:
		s.send(message)

def register(websocket):
	SCREENS.append(websocket)
	# logic for how to arrange the displays
	if not offsets:
		offsets[websocket] = [0,0]
	else: # extending displays to the right for fitwidth and fitpage
		if args.fit != 'height':
			offsets[websocket] = [-Dimensions.totalWidth, 0]
		else:
			offsets[websocket] = [0, -Dimensions.totalHeight]
	# TODO: Dimensions.totalWidth no longer a useful variable, doesn't work when screens are moved around.


	windowSizes[websocket] = (0,0)
	
	if args.filetype == 'video':
		if not VideoState.paused:
			VideoState.playbackTime += time.time() - VideoState.saveTime
		action = 'pause' if VideoState.paused else 'play'
		websocket.send(json.dumps({"type": "ctrl", "action": action, "time": VideoState.playbackTime}))
	if args.filetype == 'pdf':
		websocket.send(json.dumps({'value': str(PDFState.page), 'type': "ctrl", 'action': "pagenumberchanged"}))


def unregister(websocket):
	if currentController:
		currentController.send(json.dumps({'type': 'del', 'i': SCREENS.index(websocket)}))

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

	app.logger.info(str(len(SCREENS)) + ' connected screens');
	try:
		while not ws.closed:
			message = ws.receive()
			if not message:
				app.logger.warning('message is None')
				break
			app.logger.debug('screen message: ' + message)
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
				app.logger.debug("window size: " + str(data['w']) + "x" + str(data['h'])) # I got window size: 0x0 one time, so I should handle this
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
		app.logger.error('client (screen) disconnected - WebSocketError')
		pass
	finally:
		unregister(ws)

@app.route('/', methods=['GET'])
def index():
	if args.filetype == 'image':
		return app.send_static_file('image.html')
	if args.filetype == 'pdf':
		return app.send_static_file('pdf.html')
	# if args.filetype == 'video':
	return app.send_static_file('video.html')

allowedFits = ('width', 'height')
allowedFiletypes = ('image', 'pdf', 'video')

@app.route('/controller', methods=['GET', 'POST'])
def controller():
	if request.method == 'GET':
		return app.send_static_file('controller.html')
	else: # request.method == 'POST'
		filetypeChange = False
		if 'addnewto' in request.form and request.form['addnewto'] in allowedFits:
			args.fit = request.form['addnewto']
		if 'filetype' in request.form and request.form['filetype'] in allowedFiletypes:
			args.filetype = request.form['filetype']
			# TODO: maybe disconnect all screenClients if filetype has changed
			filetypeChange = True
		
		if filetypeChange:
			return 'Success. Please reconnect all screens'
		return 'Success'

def register_controller(ws):
	global currentController
	if currentController:
		currentController.close(1000, b'A new client was connected') # buggy function, 1000 not work
	currentController = ws
	
	i = 0
	for screen in SCREENS:
		ws.send(json.dumps({'type': 'pos', 'i': i,
		                    'x': offsets[screen][0], 'y': offsets[screen][1],
		                    'w': windowSizes[screen][0], 'h': windowSizes[screen][1]}))
		i += 1

def unregister_controller(ws):
	global currentController
	if ws == currentController:
		currentController = None

@sockets.route('/ctrller')
def controller_socket(ws):

	register_controller(ws)

	try:
		while not ws.closed:
			message = ws.receive()
			if not message:
				break
			app.logger.debug('controller message: ' + message)
			data = json.loads(message)
			try:
				if data['type'] == 'pos':
					screen = SCREENS[data['index']]
					offsets[screen][0] = data['x']
					offsets[screen][1] = data['y']
					screen.send(pos_event(screen))
			except KeyError as e:
				app.logger.error('controller KeyError: ' + e.args[0])
				
	except geventwebsocket.exceptions.WebSocketError:
		app.logger.error('client (controller) disconnected - WebSocketError')
		pass
	finally:
		unregister_controller(ws)

if __name__ != '__main__':
	gunicorn_logger = logging.getLogger('gunicorn.error')
	app.logger.handlers = gunicorn_logger.handlers
	app.logger.setLevel(gunicorn_logger.level)
#app.logger.critical('this is a CRITICAL message')

if __name__ == "__main__":

	from gevent import pywsgi
	from geventwebsocket.handler import WebSocketHandler
	server = pywsgi.WSGIServer(('', 5000), app, handler_class=WebSocketHandler)
	server.serve_forever()
