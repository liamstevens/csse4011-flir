
var canvas;
var ctx;

var ws;

var draw_busy = 0;
var frame_rate_start = 0;
var frame_rate_end = 0
var frame_rate_count = 0

var img = new Image();

$( document ).ready(function() {

    console.log( "ready!" );

    canvas = $("#myCanvas")[0]
    ctx = canvas.getContext('2d')

    canvas.height = 240
    canvas.width = 320

    $('#ViewSelect').on('change', function() {
      ws.send("!V"+this.value);
    });

    $('#Overlay').on('change', function() {
      sendInt("%", this.value);
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
      sendInt("x", this.value)
    });

    $('#OverYPos').on('change', function() {
      sendInt("Y", this.value)
    });

    $('#OverYSize').on('change', function() {
      sendInt("y", this.value)
    });

});

function sendInt(cmd, value) {
    if (value.length && parseInt(value) != NaN) {
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


      if (typeof received_msg === "string") {

        if (received_msg[0] == '!') {
          HandleCommands(received_msg)
        } else {
          $("#message").val(received_msg);
        }

      } else {
            
            var bytes = new Uint8Array(received_msg);

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
