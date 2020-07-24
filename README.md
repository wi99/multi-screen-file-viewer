
# WebSockets Multi Screen File Viewer
Displays a single image or video on multiple browser windows, which can be on different devices (mobile or desktop). It is responsive to dragging, window resizing, client connection and disconnection, and video actions (play, pause, jump). Each browser window has the image video embedded on the webpage, but what's displayed on each browser window does not overlap

## How to Run:
### Setting things up:

#### Install Dependencies:
	$ pip3 install flask-sockets

#### Generate cert and key for HTTPS:
	$ openssl req -x509 -newkey rsa:4096 -nodes -out cert.pem -keyout key.pem -days 365


### Run the webserver:

	$ gunicorn3 --certfile cert.pem --keyfile key.pem -k flask_sockets.worker -b 0.0.0.0:8080 flaskserv:app

and on different screens/windows/devices, open `https://[ip address]:8080`. For settings and moving the placement of devices, open `https://[ip address]:8080/controller` - only one client can control at a time.

 - For HTTP, remove `--certfile cert.pem --keyfile key.pem`
 - To display debug logging, add `--log-level=debug`
 - Remove `0.0.0.0` to have it only accessible locally

## TO DO:
- Speed up slow websocket / delays in message sending (generally a mobile problem)
- Improve pdf viewer: Only page navigation works currently
- Improve controller: Screen rotation, scale. Canvas zoom or increase size. Don't change rectangle color of higher indexes on removal of a screen.
- Improve video player: new screen connect but its progress wasn't moved. mobile bug where you can't choose where you want to watch.

## Attributes
Example PDF: https://commons.wikimedia.org/wiki/File:Lorem_ipsum_in_Ubuntu_20191111.pdf

Example Video: Big Buck Bunny by Blender

Example Image: https://pixabay.com/photos/rain-autumn-sunset-sun-nature-2092122/
