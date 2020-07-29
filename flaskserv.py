from flask import Flask, request, make_response, render_template, send_from_directory
from functools import wraps
from flask_sockets import Sockets
import geventwebsocket
import asyncio, time
import json, hashlib
import logging
from werkzeug.utils import secure_filename
import os

UPLOAD_FOLDER = 'uploads'
ALLOWED_MIMETYPES = {'application/pdf', 'image/', 'video/'}

app = Flask(__name__)
sockets = Sockets(app)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024 * 1024 # Default 5 GB

class View:
	x = 0
	y = 0
	width = 0
	height = 0

	screenClients = []
	offsets = {} # key: websocket, value: [x,y]. values are 0 or negative
	windowSizes = {} # key: websocket, value: (width, height)

controllerClient = None

class Params:
	def __init__(self, filepath):
		self.filepath = filepath
		self._params = {
			'authRequired': False,
			'username': 'username',
			'passwordHash': '5e884898da28047151d0e56f8dc6292773603d0d6aabbdd62a11ef721d1542d8', # same as hashlib.sha256('password'.encode('utf-8')).hexdigest()
			'videoCurrentTime': 0,
			'pdfPage': 1,
			'filetype': 'pdf',
			'constrainViewTo': 'width',
			'addNewScreensTo': 'width',
			'imageFilename': '4k.jpg',
			'videoFilename': 'video.mp4',
			'videoMimetype': 'video/mp4',
			'pdfFilename': 'document.pdf',
			
		}
		try:
			with open(filepath, 'r') as f:
				data = json.load(f)
				for key in self._params:
					if key in data and self._isValid(key, data[key]):
						self._params[key] = data[key]
		except FileNotFoundError:
			app.logger.info(f'No such file {self.filepath}. Will create one when a nondefault param is set.') # This doesn't log(), must be too early in script. print() works fine though
		except json.decoder.JSONDecodeError as e:
			app.logger.error(f'Custom Params Failed - {e}')

	def get(self, param):
		return self._params[param]

	def set(self, param, arg): # returns True if value was changed, False if value did not change, and handles invalid param/arg
		if param in self._params and self._isValid(param, arg) and self._params[param] != arg:
			self._params[param] = arg
			with open(self.filepath, 'w') as f:
				json.dump(self._params, f)
			return True
		return False
	
	allowedFiletypes = ('image', 'pdf', 'video')
	allowedConstrains = ('width', 'height', 'both')
	allowedaddNewScreensTos = ('width', 'height', 'origin')
	
	def _isValid(self, param, arg):
		if param == 'filetype' and arg not in self.allowedFiletypes:
			return False
		elif param == 'constrainViewTo' and arg not in self.allowedConstrains:
			return False
		elif param == 'addNewScreensTo' and arg not in self.allowedaddNewScreensTos:
			return False
		return True

params = Params('params.json')

class VideoState:
	lastUpdate = time.time()
	currentTime = params.get('videoCurrentTime')
	paused = True

class PDFState:
	page = params.get('pdfPage')

def pos_event(ws):
	return json.dumps(
		{"type": "pos",
		'x': View.x + View.offsets[ws][0],
		'y': View.y + View.offsets[ws][1]}
	)

def dim_event():
	if params.get('constrainViewTo') == 'width':
		return json.dumps({'type': 'dim', 'w': str(View.width) + 'px', 'h': 'auto'})
	elif params.get('constrainViewTo') == 'height':
		return json.dumps({'type': 'dim', 'w': 'auto', 'h': str(View.height) + 'px'})
	else: # params.get('constrainViewTo') == 'both'
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
		if params.get('addNewScreensTo') == 'width':
			View.offsets[websocket] = [-View.width, 0]
		elif params.get('addNewScreensTo') == 'height':
			View.offsets[websocket] = [0, -View.height]
		else: # params.get('addNewScreensTo') == 'origin'
			View.offsets[websocket] = [0, 0]

	View.windowSizes[websocket] = (0,0)
	
	if params.get('filetype') == 'video':
		if not VideoState.paused:
			VideoState.currentTime += time.time() - VideoState.lastUpdate
			params.set('videoCurrentTime', VideoState.currentTime)
		action = 'pause' if VideoState.paused else 'play'
		websocket.send(json.dumps({"type": "ctrl", "action": action, "time": VideoState.currentTime}))
	if params.get('filetype') == 'pdf':
		websocket.send(json.dumps({'value': str(params.get('pdfPage')), 'type': "ctrl", 'action': "pagenumberchanged"}))

def unregister(websocket):
	if controllerClient:
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
	if params.get('filetype') == 'video':
		if not VideoState.paused:
			VideoState.currentTime += time.time() - VideoState.lastUpdate # will be inaccurate if the last client disconnects the wrong way.
			params.set('videoCurrentTime', VideoState.currentTime)
	
	try:
		notify_pos()
		notify_dim()
	except geventwebsocket.exceptions.WebSocketError:
		app.logger.error('WebSocketError - Probably tried to send message to client that is already closed')
	finally:
		pass

def auth_required(f):
	@wraps(f)
	def decorated(*args, **kwargs):
		if not params.get('authRequired'):
			return f(*args, **kwargs)
		auth = request.authorization
		if auth and auth.username == params.get('username') and hashlib.sha256(auth.password.encode('utf-8')).hexdigest() == params.get('passwordHash'):
			return f(*args, **kwargs)
		return make_response('Could not verify your login!', 401, {'WWW-Authenticate': 'Basic realm="Login Required"'})

	return decorated

@app.route('/', methods=['GET'])
@auth_required
def index():
	if params.get('filetype') == 'image':
		return render_template('image.html', filename=params.get('imageFilename'))
	if params.get('filetype') == 'pdf':
		return render_template('pdf.html', filename=params.get('pdfFilename'))
	# video
	return render_template('video.html', filename=params.get('videoFilename'), mimetype=params.get('videoMimetype'))

@sockets.route('/sync')
@auth_required
def sync_socket(ws):
	register(ws)

	app.logger.info(str(len(View.screenClients)) + ' connected screens');
	try:
		while not ws.closed:
			message = ws.receive()
			if not message:
				app.logger.warning('message is None') # TODO: Is this normal behavior or fixable?
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
				data['filetype'] = params.get('filetype')
				notify_relay(data)
				if params.get('filetype') == 'video':
					VideoState.currentTime = data['time']
					VideoState.lastUpdate = time.time()
					params.set('videoCurrentTime', VideoState.currentTime)
					if data['action'] == 'pause':
						VideoState.paused = True
					else: # data['action'] == 'play'
						VideoState.paused = False
				if params.get('filetype') == 'pdf':
					if data['action'] == 'nextpage':
						PDFState.page += 1
					elif data['action'] == 'previouspage':
						PDFState.page -= 1
					else: # data['action'] == 'pagenumberchanged':
						PDFState.page = int(data['value'])
					params.set('pdfPage', PDFState.page)

	except geventwebsocket.exceptions.WebSocketError:
		app.logger.error('client (screen) disconnected - WebSocketError')
	finally:
		unregister(ws)

def alert(string):
	return f'<script>alert(\'{string}\')</script>'

@app.route('/controller', methods=['GET', 'POST'])
@auth_required
def controller():
	if request.method == 'GET':
		return app.send_static_file('controller.html')
	else: # request.method == 'POST'
		filetypeChange = False
		change = False
		if 'constrainviewto' in request.form:
			change = params.set('constrainViewTo', request.form['constrainviewto'])
			if change:
				notify_dim()
		if 'addnewscreensto' in request.form:
			change = params.set('addNewScreensTo', request.form['addnewscreensto']) or change
		if 'filetype' in request.form:
			filetypeChange = params.set('filetype', request.form['filetype'])
			if filetypeChange:
				for screen in View.screenClients:
					screen.close(1000, b'Filetype was Changed. Refresh Page.')

		if 'authrequired' in request.form:
			if request.form['authrequired'] == 'yes':
				change = params.set('authRequired', True) or change
			elif request.form['authrequired'] == 'no':
				change = params.set('authRequired', False) or change
		if 'username' in request.form:
			change = params.set('username', request.form['username']) or change
		if 'password' in request.form:
			change = params.set('passwordHash', hashlib.sha256(request.form['password'].encode('utf-8')).hexdigest()) or change

		if filetypeChange: # Message with more info takes priority
			return alert('Settings Changed Successfully. Please reconnect all screens')
		if change:
			return alert('Settings Changed Successfully')
		return alert('No Settings Changed')

def allowed_file(mimetype): # Note: this only checks the file extension and doesn't actually read the beginning of the file for the mimetype
	if mimetype in ALLOWED_MIMETYPES:
		return True
	for allowedMimetype in ALLOWED_MIMETYPES:
		if allowedMimetype.endswith('/') and mimetype.startswith(allowedMimetype):
			return True
		#elif allowedMimetype.startswith('/') and mimetype.endswith(allowedMimetype):
		#	return True
	return False

@app.route('/upload', methods=['POST'])
@auth_required
def upload():
	if 'file' not in request.files:
		return alert('No file part')
	
	f = request.files['file']
	
	if not f.filename:
		return alert('No selected file')
	
	mimetype = f.content_type
	if not allowed_file(mimetype):
		return alert('Filetype not allowed')
	
	filename = secure_filename(f.filename)
	
	# TODO: maybe don't delete file?
	filenameChanged = False
	oldFilename = None
	if mimetype == 'application/pdf':
		oldFilename = params.get('pdfFilename')
		filenameChanged = params.set('pdfFilename', filename)
	elif mimetype.startswith('image/'):
		oldFilename = params.get('imageFilename')
		filenameChanged = params.set('imageFilename', filename)
	elif mimetype.startswith('video/'):
		oldFilename = params.get('videoFilename')
		filenameChanged = params.set('videoFilename', filename)
		params.set('videoMimetype', mimetype)
	
	if not os.path.exists('uploads'):
		os.makedirs('uploads')
	filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
	f.save(filepath)
	app.logger.info(f'saved file {filepath}')
	
	if filenameChanged:
		try:
			oldFilepath = os.path.join(app.config['UPLOAD_FOLDER'], oldFilename)
			os.remove(oldFilepath)
			app.logger.info(f'deleted file {oldFilepath}')
		except FileNotFoundError as e:
			app.logger.error(e)

	return alert('file uploaded successfully')

@app.route('/uploads/<filename>')
@auth_required
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

def register_controller(ws):
	global controllerClient
	if controllerClient:
		controllerClient.close(1000, b'A new client was connected') # buggy function, I don't get 1000 on the other end
	controllerClient = ws
	
	# try catch over here in case a client is not connected but still listed?
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
@auth_required
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
