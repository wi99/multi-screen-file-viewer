# WebSockets Multi Screen File Viewer
Displays a single image or video on multiple browser windows, which can be on different devices (mobile or desktop). It is responsive to dragging, window resizing, client connection and disconnection, and video actions (play, pause, jump). Each browser window has the image video embedded on the webpage, but what's displayed on each browser window does not overlap

## How to Run:
Setting things up:

	$ pip3 install flask-sockets

Run the webserver:

	$ gunicorn3 -k flask_sockets.worker -b 0.0.0.0 flaskserv:app

and open http://[ip address]:8000

Run it only locally, custom port 8080:

	$ gunicorn3 -k flask_sockets.worker -b :8080 flaskserv:app

## TO DO:
- Speed up slow websocket / delays in message sending
- The user to be able to change what is viewed from the web browser, including file upload, file type being viewed, and screens placement.
- Improve pdf viewer

## Attributes
Example PDF: https://commons.wikimedia.org/wiki/File:Lorem_ipsum_in_Ubuntu_20191111.pdf

Example Video: Big Buck Bunny by Blender

Example Image: https://pixabay.com/photos/rain-autumn-sunset-sun-nature-2092122/ 
