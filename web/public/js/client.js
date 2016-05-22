
var canvas;
var ctx;



$( document ).ready(function() {
    console.log( "ready!" );

    canvas = $("#myCanvas")[0]
    ctx = canvas.getContext('2d')

    canvas.height = 480
    canvas.width = 640

});

function drawPGM (data) {

  let lines = data.split("\n")  

  let width = lines[1].split(" ")[0]
  let height = lines[1].split(" ")[1]
  let maxValue = lines[2]

  let canvas = $("#myCanvas")[0]
  let ctx = canvas.getContext('2d')

  canvas.height = 480
  canvas.width = 640
  
  let imageData = ctx.createImageData(width, height)
  let pixels = imageData.data

  for (let y = 0; y < height; y++) {

    row_data = lines[3+y].split(" ")


    for (let x = 0; x < width; x++) {
      let rawValue = row_data[x]
      let grayValue = rawValue / maxValue * 255
      let pixelAddress = (x + y * width) * 4
      pixels[pixelAddress] = grayValue
      pixels[pixelAddress + 1] = grayValue
      pixels[pixelAddress + 2] = grayValue
      pixels[pixelAddress + 3] = 255
    }
  }

  ctx.putImageData(imageData, 0, 0)
}

function drawJPG (data) {
  var blob = new Blob([data], {type: "image/jpeg"});
  var objectURL = URL.createObjectURL(blob);

  var img = new Image();

  img.onload = function() {
    /// draw image to canvas
    ctx.drawImage(this, 0, 0);
    URL.revokeObjectURL(objectURL);
  }
  img.src = objectURL;
}

if ("WebSocket" in window)
{
   console.log("WebSocket is supported by your Browser");
   
   // Let us open a web socket
   var ws = new WebSocket("ws://localhost:8081/");
   ws.binaryType = "arraybuffer";
	
   ws.onopen = function()
   {
      // Web Socket is connected, send data using send()
      ws.send("Message to send");
      console.log("Message is sent...");
   };
	
   ws.onmessage = function (evt) 
   { 
      var received_msg = evt.data;


      if (typeof received_msg === "string") {
        var string = received_msg
        $("#message").val(string);
      } else {
            
            var bytes = new Uint8Array(received_msg);

            drawJPG(bytes)

            // var string = new TextDecoder("utf-8").decode(bytes);
            // drawPGM(string);
          
      }

      // console.log("Message is received...");
      
   };
	
   ws.onclose = function()
   { 
      // websocket is closed.
      console.log("Connection is closed..."); 
   };
}

else
{
   // The browser doesn't support WebSocket
   console.log("WebSocket NOT supported by your Browser!");
}
