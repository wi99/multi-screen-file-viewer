# WebSockets Multi Screen File Viewer
Displays a single image or video on multiple browser windows, which can be on different devices (mobile or desktop). It is responsive to dragging, window resizing, client connection and disconnection, and video actions (play, pause, jump). Each browser window has the image video embedded on the webpage, but what's displayed on each browser window does not overlap

## How to Run:
In Terminal:

	$ python3 serv.py

In the web browser:
Open index.html,

Or run a webserver:

	$ python3 -m http.server 8000

and open http://localhost:8000

But you get better results when files are locally available on each device, so change the websockets address in index.html, download this onto each device, and open index.html.


## Attributes
Example PDF: https://commons.wikimedia.org/wiki/File:Lorem_ipsum_in_Ubuntu_20191111.pdf
Example Video: Big Buck Bunny by Blender
Example Image: https://pixabay.com/photos/rain-autumn-sunset-sun-nature-2092122/ 
