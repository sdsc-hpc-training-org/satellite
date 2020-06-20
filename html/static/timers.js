var ttl = 10;
var timerHandle;

// updates the timeRemaining element, will
// reload when ttl = 0
// call with window.setInterval()
function countdownReload()
{
  ttl--;
  e = document.getElementById('timeRemaining');
  e.innerHTML = ttl;
  if ( ttl == 0 ) 
  {
    location.reload();
  }
}

// stops the countdown and thus the reloading.
function stopReload()
{
  window.clearTimeout(timerHandle);
  e = document.getElementById('timeRemaining');
  e.innerHTML = "Stopped (reload to continue)";
  e = document.getElementById('pauseButton');
  e.remove();
}

