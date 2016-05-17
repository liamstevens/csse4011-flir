
function drawPGM (data) {

  let lines = data.split("\n")  

  let width = lines[1].split(" ")[0]
  let height = lines[1].split(" ")[1]
  let maxValue = lines[2]

  let canvas = $("#myCanvas")[0]
  let ctx = canvas.getContext('2d')

  canvas.height = 60
  canvas.width = 80
  
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

if ("WebSocket" in window)
{
   console.log("WebSocket is supported by your Browser!");
   
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
            var string = new TextDecoder("utf-8").decode(bytes);
            drawPGM(string);
          
      }

      console.log("Message is received...");
      
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
