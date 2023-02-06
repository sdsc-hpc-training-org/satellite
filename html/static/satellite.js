var starttl = 100;
var ttl = 100;
var refilling = false;
var tokenstateurl = 'https://apples.sdsc.edu/tokenjobstate.cgi?token=';

window.addEventListener('DOMContentLoaded', () => {
    window.setInterval(countdownReload,50);
    });


// updates the timerWheel element, will
// triggers loadState when timerWheel is empty.
// call with window.setInterval()
// there are 100 steps in the timerWheel, this will
// decrement by 1 and increment by 10 when refilling
// interval determines how long the timer runs!
function countdownReload()
{
    tw = document.getElementById('timerWheel');

    if ( refilling )
    {
        ttl += 10;
    } else
    {
        ttl -= 1;
    }

    if ( ttl < 0 ) 
    {
        refilling = true;
        ttl = 0;
        loadStatus();
    }

    if ( ttl > starttl )
    {
        refilling = false;
        ttl = starttl;
    }

    cn = "progress-circle p" + ttl;
    if ( ttl > 50 )
    {
        cn += " over50";
    }
    tw.className = cn;
}



// convert tokenjobstate.cgi output to
// a stepList index.
//
// special indices:
// -1: unknown
// -2: job is dead, never going to proceed.
function jobState2StepList(s)
{
    switch(s)
    {
        // basic codes, always available

        // pending: all we know is it's not mapped yet
        // so "in queue"
        case 'PE':
        return { index: 0, text: 'In Queue'};

        // mapped
        case 'M':
        return { index: 2, text: 'Mapped'};

        // proxied
        case 'PR':
        return { index: 3, text: 'Proxied'};

        // extended codes, requires api call to bind jobid to token

        // in queue for sure
        case 'Q':
        return { index: 0, text: 'In Queue'};

        // running but not mapped
        case 'R':
        return { index: 1, text: 'Running'};

        // dead
        case 'D':
        return { index: -2, text: 'Dead'};

        // unknown!
        default:
        return { index: -1, text: 'Unknown'};
    }
}


// set the progress bar thing
// call with object literal having these fields:
//   index: step number s (0-based)
//   text: textual display name of state
// will set the s'th and previous to 'active' class
// unless certain conditions are met (unknown, dead)
// will set textual description of state as well.
function setProgress(s)
{  
    e = document.getElementById('jobStateText');
    e.textContent = s.text;
    e = document.getElementById('stepList');
    lis = e.children;
    for( i = 0; i < lis.length; i++ )
    {
        if ( s.index == -2  )
        {
            if ( lis[i].className != 'active' )
                lis[i].setAttribute('class', 'dead');
        } else
        {
            // the -1/unknown state is handled here implicitly
            // all steps will be inactive.
            if ( i <= s.index )
            {
                lis[i].setAttribute('class', 'active');
            } else
            {
                lis[i].removeAttribute('class');
            }
        }
    }
}


function loadStatus()
{
    xhr = new XMLHttpRequest();
    xhr.onreadystatechange = function() {
        if ( this.readyState == 4 && this.status == 200 ) {
            step = jobState2StepList(xhr.responseText);
            setProgress(step);
            if ( step.text == 'Proxied' ) location.reload();
        }
    }
    url = tokenstateurl;
    url += window.location.hostname;
    xhr.open("GET", url, true);
    xhr.send();
}

