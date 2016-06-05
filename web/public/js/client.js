
// Websocket connection
var ws;

// Canvas to draw onto
var canvas;
var ctx;

// Image to buffer canvas data
var img = new Image();

// Used to only attempt a draw, if not already doing so
var draw_busy = 0;

// Used for framerate calculation
var frame_rate_start = 0;
var frame_rate_end = 0
var frame_rate_count = 0

$( document ).ready(function() {

    console.log( "ready!" );

    // Do this firts, and only once, for efficiency.
    canvas = $("#myCanvas")[0]
    ctx = canvas.getContext('2d')

    canvas.height = 240
    canvas.width = 320

    // Register all the onchange function events

    $('#ViewSelect').on('change', function() {
      ws.send("!V"+this.value);
    });

    $('#Overlay').on('change', function() {
      sendPositiveInt("%", this.value);
    });

    $('#FlipX').on('change', function() {
      ws.send("!O" + ((this.checked == true) ? 1 : 0));
    });

    $('#FlipY').on('change', function() {
      ws.send("!U" + ((this.checked == true) ? 1 : 0));
    });

    $('#MultiFD').on('change', function() {
      ws.send("!M" + ((this.checked == true) ? 1 : 0));
    });

    $('#Colorize').on('change', function() {
      ws.send("!C" + ((this.checked == true) ? 1 : 0));
    });

    $('#Save').on('change', function() {
      ws.send("!S" + ((this.checked == true) ? 1 : 0));
    });

    $('#OverXPos').on('change', function() {
      sendInt("X", this.value)
    });

    $('#OverXSize').on('change', function() {
      sendPositiveInt("x", this.value)
    });

    $('#OverYPos').on('change', function() {
      sendInt("Y", this.value)
    });

    $('#OverYSize').on('change', function() {
      sendPositiveInt("y", this.value)
    });

});

// Send int if valid value
function sendInt(cmd, value) {
    if (value.length && parseInt(value) != NaN) {
      ws.send("!"+cmd+value);
    }
}

// Sent int if valid positive value
function sendPositiveInt(cmd, value) {
    if (value.length && parseInt(value) != NaN && parseInt(value) > 0) {
      ws.send("!"+cmd+value);
    }
}

function drawJPG (data) {

  draw_busy = 1;

  var blob = new Blob([data], {type: "image/jpeg"});
  var objectURL = URL.createObjectURL(blob);

  img.onload = function() {
    /// draw image to canvas
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    ctx.drawImage(this, 0, 0);
    URL.revokeObjectURL(objectURL);
    this.src = "";
    draw_busy = 0;
  }
  img.src = objectURL;
}


if ("WebSocket" in window)
{
   console.log("WebSocket is supported by your Browser");
   
   // Let us open a web socket
   ws = new WebSocket("ws://"+window.location.hostname+":8081/");
   console.log("Connected to: " + "ws://"+window.location.hostname+":8081/")
   ws.binaryType = "arraybuffer";
	
   ws.onopen = function()
   {
      // Web Socket is connected, send data using send()
      $("#HeaderConnectionStatus").text(" - Connected ")

      ws.send("Message to send");
      console.log("Message is sent...");
   };
	
   ws.onmessage = function (evt) 
   { 
      var received_msg = evt.data;

      // If we received a string, ...
      if (typeof received_msg === "string") {

        // check for command message
        if (received_msg[0] == '!') {
          HandleCommands(received_msg)
        } 

        // Otherwise probably debugging message
        else {
          $("#message").val(received_msg);
        }

      } 

      // If data from opencv in ArrayBuffer,
      else {
        
        // Convert to Uint8_t array
        var bytes = new Uint8Array(received_msg);

        // If have the \x40\x11 magic bytes, its heartbeat data
        if (bytes[0] == 0x40 && bytes[1] == 0x11 ) {

          str_bytes = new Uint8Array(received_msg,2);
          msg = new TextDecoder('utf-8').decode(str_bytes);
          $("#message").val(msg);

        } 

        // Else if it has the \xFF\xD8 magic numberm its JPG
        else if (bytes[0] == 0xFF && bytes[1] == 0xD8 ) {

          if (!draw_busy) {
            drawJPG(bytes)
          }

          if (frame_rate_count == 0) {
            frame_rate_start = new Date().getTime();
          } else if (frame_rate_count == 9) {
            frame_rate_end = new Date().getTime();

            delta = (frame_rate_end - frame_rate_start);
            fps = 10 / (delta/1000.0);
            $("#FPS").val(fps);
          }

          frame_rate_count = (frame_rate_count + 1) % 10;

        } 

        // Otherwise, trash it
        else {

          console.log("Unkown Data");

        }

      }

   };
	
   ws.onclose = function()
   { 
      // websocket is closed.
      console.log("Connection is closed..."); 
      $("#HeaderConnectionStatus").text(" - Disconnected ")
   };
}

else
{
   // The browser doesn't support WebSocket
   console.log("WebSocket NOT supported by your Browser!");
   $("#HeaderConnectionStatus").text(" - WS NOT SUPPORTED ")
}

function HandleCommands (cmd) {

  switch(cmd[1]) {

    case 'V':
      $('#ViewSelect').val(cmd[2]);
      break;

    case '%':
      $('#Overlay').val(cmd.substring(2));
      break;

    case 'O':
      $("#FlipX").prop('checked', ((cmd[2] == 1) ?  true : false));
      break;

    case 'U':
      // $('.myCheckbox').is(':checked');
      $("#FlipY").prop('checked', ((cmd[2] == 1) ?  true : false));
      break;

    case 'M':
      $("#MultiFD").prop('checked', ((cmd[2] == 1) ?  true : false));
      break;

    case 'C':
      // $('.myCheckbox').is(':checked');
      $("#Colorize").prop('checked', ((cmd[2] == 1) ?  true : false));
      break;

    case 'S':
      $("#Save").prop('checked', ((cmd[2] == 1) ?  true : false));
      break;

    case 'X':
      $('#OverXPos').val(cmd.substring(2));
      break;

    case 'x':
      $('#OverXSize').val(cmd.substring(2));
      break;

    case 'Y':
      $('#OverYPos').val(cmd.substring(2));
      break;

    case 'y':
      $('#OverYSize').val(cmd.substring(2));
      break;

    default:
      break;

  }

}
