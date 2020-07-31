var fullscreenToggle = document.getElementById('fullscreenToggle')
var fullscreenToggleVisibilityTimer = setTimeout(function(){
  fullscreenToggle.style.visibility = 'hidden'
}, 5000) // for some reason this settimeout doesn't work well on mobile and I still see the button, but the other settimeouts work fine

fullscreenToggle.onclick = openFullscreen;

window.addEventListener('resize', function(event){
  fullscreenToggle.style.visibility = 'visible'

  clearTimeout(fullscreenToggleVisibilityTimer)
  fullscreenToggleVisibilityTimer = setTimeout(function(){
    fullscreenToggle.style.visibility = 'hidden'
  }, 5000)
});

var elem = document.documentElement;
function openFullscreen() {
  if (elem.requestFullscreen) {
    elem.requestFullscreen();
  } else if (elem.mozRequestFullScreen) { /* Firefox */
    elem.mozRequestFullScreen();
  } else if (elem.webkitRequestFullscreen) { /* Chrome, Safari & Opera */
    elem.webkitRequestFullscreen();
  } else if (elem.msRequestFullscreen) { /* IE/Edge */
    elem.msRequestFullscreen();
  }
}

function closeFullscreen() {
  if (document.exitFullscreen) {
    document.exitFullscreen();
  } else if (document.mozCancelFullScreen) {
    document.mozCancelFullScreen();
  } else if (document.webkitExitFullscreen) {
    document.webkitExitFullscreen();
  } else if (document.msExitFullscreen) {
    document.msExitFullscreen();
  }
}

document.addEventListener('fullscreenchange', (event) => {
  if (document.fullscreenElement) {
    fullscreenToggle.innerHTML = '<p>↘↙<br>↗↖</p>'
    fullscreenToggle.onclick = closeFullscreen;
  } else {
    fullscreenToggle.innerHTML = '<p>↖↗<br>↙↘</p>'
    fullscreenToggle.onclick = openFullscreen;
  }
});

