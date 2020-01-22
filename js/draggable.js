// https://stackoverflow.com/a/11409944
Number.prototype.clamp = function(min, max) {
  return Math.min(Math.max(this, min), max);
};

var selfMove = false;
var div = document.getElementById("container");
//Make the DIV element draggable:
dragElement(div);

var video = document.getElementById('display');

var cc = document.getElementById('controlsContainer')

if (!window.location.hostname)
  websocket = new WebSocket("ws://localhost:" + WEBSOCKETS_PORT);
else
  websocket = new WebSocket("ws://" + window.location.hostname + ":" + WEBSOCKETS_PORT);

function sendDim(event) {
  var width = Math.min(window.innerWidth, window.outerWidth); // android 4.4 chrome where outerWidth is correct and innerWidth too big
  var height = Math.min(window.innerHeight, window.outerHeight);
  websocket.send(JSON.stringify({type: 'dim', w: width, h: height}));
};
window.onresize = sendDim;
websocket.onopen = sendDim;

websocket.onmessage = function(event) {
  data = JSON.parse(event.data);
  switch (data.type) {
    case 'pos':
      if (!selfMove){
        div.style.top = data.y + "px";
        div.style.left = data.x + "px";
      }
      break;
    case 'dim':
      div.style.width = data.w;
      div.style.height = data.h;
      div.dispatchEvent(new CustomEvent('resize'));
      break;
    case 'ctrl':
      // VIDEO
      switch (data.filetype) {
        case 'video':
          video.currentTime = data.time;
          switch (data.action){
            case 'pause':
              video.pause();
              break;
            case 'play':
              video.play();
              break;
            }
          break;
        case 'pdf':
          //data.source = 'ws';
          eventBus.dispatch(data.action, data);
          break;
      }
      break;
    default:
      console.error(
        "unsupported event", data);
  }
};

function dragElement(elmnt) { // elmnt is div, elmnt.children[0] is img
  var currentX, currentY, initialX, initialY;
  elmnt.onmousedown = elmnt.ontouchstart = dragStart;

  function dragStart(e) {
    cc.style.pointerEvents = 'none'; // I was hoping this would prevent accidental clicks but it does not.
    e = e || window.event;
    if (e.type != "touchstart") e.preventDefault();
    if (e.type === "touchstart") {
      initialX = e.touches[0].clientX;
      initialY = e.touches[0].clientY;
    } else {
      initialX = e.clientX;
      initialY = e.clientY;
    }
    selfMove = true;
    // call a function whenever the cursor moves:
    document.onmousemove = document.ontouchmove = elementDrag;
    document.onmouseup = document.ontouchend = dragEnd;
  }

  function elementDrag(e) {
    e = e || window.event;
    if (e.type != "touchmove") e.preventDefault();
    if (e.type === "touchmove") {
      currentX = e.touches[0].clientX - initialX;
      currentY = e.touches[0].clientY - initialY;
      initialX = e.touches[0].clientX;
      initialY = e.touches[0].clientY;
    } else {
      currentX = e.clientX - initialX;
      currentY = e.clientY - initialY;
      initialX = e.clientX;
      initialY = e.clientY;
    }
    // set the element's new position:
    var width = Math.min(window.innerWidth, window.outerWidth);
    var height = Math.min(window.innerHeight, window.outerHeight);
    var y = Math.round((elmnt.offsetTop + currentY).clamp(40-elmnt.offsetHeight, height-40));
    var x = Math.round((elmnt.offsetLeft + currentX).clamp(40-elmnt.offsetWidth, width-40));
    elmnt.style.top = y + "px";
    elmnt.style.left = x + "px";
    websocket.send(JSON.stringify({type: 'pos', x: x, y: y}));
  }

  function dragEnd(e) {
    cc.style.pointerEvents = 'auto';
    selfMove = false;
    /* stop moving when mouse button is released:*/
    document.onmouseup = document.ontouchend = null;
    document.onmousemove = document.ontouchmove = null;
  }
  /*
  var i=0
  // https://developer.mozilla.org/en-US/docs/Web/API/Element/wheel_event
  function zoom(event) {
    event.preventDefault();

    scale += event.deltaY * -0.001; // Not sure if instead should have wheel linearly control the size, instead of based on multiplier (since change is exponential)
    console.log(event.deltaY)

    // Restrict scale
    scale = scale.clamp(0.02, 4);

    // Apply scale transform
    elmnt.style.transform = `scale(${scale})`;
  }

  let scale = 1;
  elmnt.onwheel = zoom;
  */
  
}
