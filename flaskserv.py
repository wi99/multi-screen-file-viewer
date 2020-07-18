from flask import Flask
from flask_sockets import Sockets
from flask import request
import geventwebsocket
import asyncio, time, json
import logging

app = Flask(__name__)
sockets = Sockets(app)

class View:
	x = 0
	y = 0
	width = 0
	height = 0

	screenClients = []
	offsets = {} # key: websocket, value: x,y. values are 0 or negative
	windowSizes = {} # key: websocket, value: (width, height)

controllerClient = None

# TODO: make these persist after exiting program.
class VideoState:
	saveTime = time.time()
	playbackTime = 0
	paused = True

class PDFState:
	page = 1

class args:
	filetype = 'pdf' # 'image', 'pdf', or 'video'
	constrain = 'width' # 'width', 'height', or 'both'
	addNewScreensTo = 'width' # 'height', 'origin'

def pos_event(ws):
	return json.dumps(
		{"type": "pos",
		'x': View.x + View.offsets[ws][0],
		'y': View.y + View.offsets[ws][1]}
	)

def dim_event():
	if args.constrain == 'width':
		return json.dumps({'type': 'dim', 'w': str(View.width) + 'px', 'h': 'auto'})
	elif args.constrain == 'height':
		return json.dumps({'type': 'dim', 'w': 'auto', 'h': str(View.height) + 'px'})
	else: # args.constrain == 'both'
		return json.dumps({'type': 'dim', 'w': str(View.width) + 'px', 'h': str(View.height) + 'px'})

def action_event(action):
	return json.dumps({'type': 'ctrl', 'action': action})

def notify_pos():
	for screen in View.screenClients:
		screen.send(pos_event(screen))

def notify_dim():
	message = dim_event()
	for s in View.screenClients:
		s.send(message)
	
		if controllerClient:
			controllerClient.send(json.dumps({'type': 'pos', 'i': View.screenClients.index(s), 'x': View.offsets[s][0], 'y': View.offsets[s][1], 'w': View.windowSizes[s][0], 'h': View.windowSizes[s][1]}))

def notify_relay(data):
	message = json.dumps(data)
	for s in View.screenClients:
		s.send(message)

def register(websocket):
	View.screenClients.append(websocket)
	# logic for how to arrange the displays
	if not View.offsets:
		View.offsets[websocket] = [0,0]
	else:
		if args.addNewScreensTo == 'width':
			View.offsets[websocket] = [-View.width, 0]
		elif args.addNewScreensTo == 'height':
			View.offsets[websocket] = [0, -View.height]
		else: # args.addNewScreensTo == 'origin'
			View.offsets[websocket] = [0, 0]

	View.windowSizes[websocket] = (0,0)
	
	if args.filetype == 'video':
		if not VideoState.paused:
			VideoState.playbackTime += time.time() - VideoState.saveTime
		action = 'pause' if VideoState.paused else 'play'
		websocket.send(json.dumps({"type": "ctrl", "action": action, "time": VideoState.playbackTime}))
	if args.filetype == 'pdf':
		websocket.send(json.dumps({'value': str(PDFState.page), 'type': "ctrl", 'action': "pagenumberchanged"}))

def unregister(websocket):
	if controllerClient:
		# TODO: fix error websocket object not in list when i change filetype
		controllerClient.send(json.dumps({'type': 'del', 'i': View.screenClients.index(websocket)}))

	# remove from dictionaries
	View.screenClients.remove(websocket)
	w,h = View.windowSizes.pop(websocket, (0,0))
	
	# rearrange displays
	x,y = View.offsets.pop(websocket, (0,0))
	for screen in View.screenClients: # affected offsets are those to the right aka more negative
		if View.offsets[screen][0] < x:
			View.offsets[screen][0] += w

	# resize viewer
	if View.screenClients:
		View.width = max({k: -View.offsets.get(k, 0)[0] + View.windowSizes.get(k, 0)[0] for k in set(View.offsets)}.values())
		View.height = max({k: -View.offsets.get(k, 0)[1] + View.windowSizes.get(k, 0)[1] for k in set(View.offsets)}.values())
	else:
		View.width = 0
		View.height = 0


	# reset and revert values
	if not View.screenClients:
		# general
		View.x = View.y = 0
	
	# save values
	if args.filetype == 'video':
		if not VideoState.paused:
			VideoState.playbackTime += time.time() - VideoState.saveTime # will be inaccurate if the last client disconnects the wrong way.
	
	try:
		notify_pos()
		notify_dim()
	except geventwebsocket.exceptions.WebSocketError:
		app.logger.error('WebSocketError - Probably tried to send message to client that is already closed')
	finally:
		pass

@sockets.route('/sync')
def sync_socket(ws):
	register(ws)

	app.logger.info(str(len(View.screenClients)) + ' connected screens');
	try:
		while not ws.closed:
			message = ws.receive()
			if not message:
				app.logger.warning('message is None')
				break
			app.logger.debug('screen message: ' + message)
			data = json.loads(message)
			if data['type'] == 'pos':
				View.x = data['x'] - View.offsets[ws][0]
				View.y = data['y'] - View.offsets[ws][1]
				notify_pos()

			elif data['type'] == 'dim':
				delta_x = data['w'] - View.windowSizes[ws][0]
				delta_y = data['h'] - View.windowSizes[ws][1]
				# TODO: Fix this:
				# this loop doesn't quite work well with add new screens to origin,
				# as it pushes a screen too much so that there's a space between two screens,
				# but I still need it when resize
				# same for L shape layout and then you remove a screen on the L where x=0
				for screen in View.screenClients:
					if View.offsets[screen][0] < View.offsets[ws][0]:
						View.offsets[screen][0] -= delta_x
				View.windowSizes[ws] = (data['w'], data['h'])
				View.width = max({k: -View.offsets.get(k, 0)[0] + View.windowSizes.get(k, 0)[0] for k in set(View.offsets)}.values())
				View.height = max({k: -View.offsets.get(k, 0)[1] + View.windowSizes.get(k, 0)[1] for k in set(View.offsets)}.values())
				app.logger.debug("window size: " + str(data['w']) + "x" + str(data['h']))
				if View.windowSizes[ws] == (0,0):
					app.logger.warning("window size is 0x0") # this happened once, I should do something else with it
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

allowedFiletypes = ('image', 'pdf', 'video')
allowedConstrains = ('width', 'height', 'both')
allowedaddNewScreensTos = ('width', 'height', 'origin')

@app.route('/controller', methods=['GET', 'POST'])
def controller():
	if request.method == 'GET':
		return app.send_static_file('controller.html')
	else: # request.method == 'POST'
		filetypeChange = False
		change = False
		if 'constrainviewto' in request.form and request.form['constrainviewto'] in allowedConstrains and args.constrain != request.form['constrainviewto']:
			args.constrain = request.form['constrainviewto']
			change = True
			notify_dim()
		if 'addnewscreensto' in request.form and request.form['addnewscreensto'] in allowedaddNewScreensTos and args.addNewScreensTo != request.form['addnewscreensto']:
			args.addNewScreensTo = request.form['addnewscreensto']
			change = True
		if 'filetype' in request.form and request.form['filetype'] in allowedFiletypes and args.filetype != request.form['filetype']:
			args.filetype = request.form['filetype']
			for screen in View.screenClients:
				screen.close(1000, b'Filetype in View was Changed')
			filetypeChange = True
		
		if filetypeChange:
			return 'Settings Changed Successfully. Please reconnect all screens'
		if change:
			return 'Settings Changed Successfully'
		return 'No Settings Changed'

def register_controller(ws):
	global controllerClient
	if controllerClient:
		controllerClient.close(1000, b'A new client was connected') # buggy function, I don't get 1000 on the other end
	controllerClient = ws
	
	# TODO: try catch over here in case a client that is not connected but still listed
	i = 0
	for screen in View.screenClients:
		ws.send(json.dumps({'type': 'pos', 'i': i,
		                    'x': View.offsets[screen][0], 'y': View.offsets[screen][1],
		                    'w': View.windowSizes[screen][0], 'h': View.windowSizes[screen][1]}))
		i += 1

def unregister_controller(ws):
	global controllerClient
	if ws == controllerClient:
		controllerClient = None

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
					screen = View.screenClients[data['index']]
					View.offsets[screen][0] = data['x']
					View.offsets[screen][1] = data['y']
					screen.send(pos_event(screen))
					View.width = max({k: -View.offsets.get(k, 0)[0] + View.windowSizes.get(k, 0)[0] for k in set(View.offsets)}.values())
					View.height = max({k: -View.offsets.get(k, 0)[1] + View.windowSizes.get(k, 0)[1] for k in set(View.offsets)}.values())
					notify_dim()

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
