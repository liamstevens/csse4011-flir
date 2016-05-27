/* INCLUDES */
var express = require('express');
var app = express();
var net = require('net');
var fs = require('fs');
var unix = require('unix-dgram');

/* CONST VARIABLES */
srv_path = "/run/shm/cv2node"
cli_path = "/run/shm/node2cv"

/* WEB SERVER */
app.use(express.static('public'));

app.listen(8080, function () {
  console.log('Example app listening on port 8080!');
});

/* DATAGRAM CONNECTION */
try { 
  fs.unlinkSync(srv_path);
  fs.unlinkSync(srv_path);
} catch (ex) { }

var srv_sock = unix.createSocket('unix_dgram');
var cli_sock = unix.createSocket('unix_dgram');
cli_sock_connected = 0;

srv_sock.on('message', (msg) => {
  wss.broadcast(msg);
});

srv_sock.on('error', function(e) {
  console.log(`sock got err: ${e}`);
});

srv_sock.bind(srv_path);


/* WEBSOCKET SERVER */
var WebSocketServer = require('ws').Server
var wss = new WebSocketServer({ port: 8081 });

// System state variables for new connections
var last_view_cmd = "";

wss.on('connection', function connection(ws) {

  ws.on('message', function incoming(message) {
    console.log('received: %s', message);

    // If command received from web client, handle it
    if (message[0] == '!') {
      HandleCommands(message);
    }
  });

  // Push out system state to new connections
  ws.send(last_view_cmd);

});

wss.broadcast = function broadcast(data) {
  wss.clients.forEach(function each(client) {
    client.send(data);
  });
};

function HandleCommands (cmd) {

  var broadcast = 0;
  var opencv = 0;

  switch(cmd[1]) {

    case 'V':
      last_view_cmd = cmd;
      broadcast = 1;
      opencv = 1;
      console.log(`Got view cmd`);
      break;

    default:
      console.log(`Got unknown cmd`);
      break;
  }

  // Send command to all other clients
  if (broadcast) {
    console.log(`Broadcast`);
    wss.broadcast(cmd);
  }

  // Send command back to OpenCV
  if (opencv) {
    console.log(`OpenCV`);
    var buf = Buffer(cmd);
    cli_sock.send(buf , 0, buf.length, cli_path);
  }

} 