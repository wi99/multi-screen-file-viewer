# Multi Screen File Viewer
Displays a single image or video on multiple browser windows, which can be on different devices (mobile or desktop). It is responsive to dragging, window resizing, client connection and disconnection, and video actions (play, pause, jump).
## Features
- Persistent storage: the user specified settings, the PDF page, and the video current time is saved
- Hosts 3 files at a time – one of each type (image, video, PDF)

## How to Run:
### Setting things up:

#### Install Dependencies:
	$ pip3 install gunicorn flask-sockets

#### Generate cert and key for HTTPS:
	$ openssl req -x509 -newkey rsa:4096 -nodes -out cert.pem -keyout key.pem -days 365

### Run the webserver:

	$ gunicorn3 --certfile cert.pem --keyfile key.pem -k flask_sockets.worker -b 0.0.0.0:8080 flaskserv:app

 - For HTTP, remove `--certfile cert.pem --keyfile key.pem`
 - To display debug logging, add `--log-level=debug`
 - Remove `0.0.0.0` to have it only accessible locally

## The Client (screen/device)
- On different screens/windows/devices, open `https://[ip address]:8080`.
- All filetypes:
  - Use mouse or touch to drag the image/video/PDF.
  - For the first 5 seconds of loading the page, a full screen toggle button will appear in the bottom right corner. To make it reappear, resize the browser window (switch orientation for mobile). It will stay visible for 5 seconds after the resize.
- Video viewer:
  - Bring the controls up: Move the mouse pointer around the top or tap the top right corner.
  - Bring the controls away: Move the mouse pointer away from the top or tap somewhere in the page other than the top.
- PDF viewer:
  - To change pages, use the previous page and next page buttons, or specify it in the textbox.

## The Controller
- For settings and moving the placement of devices, open `https://[ip address]:8080/controller`
- Only one client can use the controller at a time.
### Screen Placement Adjuster
Click and drag a screen to make something like a 2x2 or a 4x4 grid, or anything that is not in a single line.
### Transform Screen
After a screen is selected, you can specify a position for the screen (instead of dragging with the mouse).
### Draggable Container
The **Reset Placement** button resets the placement of the image/video/PDF
### Viewer Settings
- By default, a new screen is added to the right of the rightmost screen, and when a screen is removed, the others are shifted. The controller has options where to add new screens and whether to rearrange the screens when a screen changes in size or is removed.
- Change file type to be viewed.
### Authentication Settings
- HTTPS recommended if submitting a username/password
- Default username: username
- Default password: password
### File Upload
Not too big video file recommended because each client downloads the whole video before playing it (this helps with syncing).

## Attributes
- Example PDF: https://commons.wikimedia.org/wiki/File:Lorem_ipsum_in_Ubuntu_20191111.pdf
- Example Video: Big Buck Bunny by Blender
- Example Image: https://pixabay.com/photos/rain-autumn-sunset-sun-nature-2092122/


## TO DO:
- Improve pdf viewer: Only page navigation works currently
- Improve controller: Screen rotation, scale. Canvas zoom or increase size. Don't change rectangle color of higher indexes on removal of a screen.
- Improve video player: new screen connect but its progress wasn't moved.
- Handle bad disconnections e.g. wifi disconnected on a screen (ping and timeout and stuff)
- manual offset to improve syncing
- video currentTime set on newly connected client stopped working after I implemented preloading the video
