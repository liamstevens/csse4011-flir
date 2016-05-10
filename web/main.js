
var express = require('express');
var app = express();

app.use(express.static('public'));

app.listen(8080, function () {
  console.log('Example app listening on port 8080!');
});



const dgram = require('dgram');
const server = dgram.createSocket('udp4');

server.on('error', (err) => {
  console.log(`server error:\n${err.stack}`);
  server.close();
});

server.on('message', (msg, rinfo) => {
  console.log(`server got: msg from ${rinfo.address}:${rinfo.port}`);
  //console.log(`server got: ${msg} from ${rinfo.address}:${rinfo.port}`);

  wss.broadcast(msg);
});

server.on('listening', () => {
  var address = server.address();
  console.log(`server listening ${address.address}:${address.port}`);
});

server.bind(41234);
// server listening 0.0.0.0:41234

var WebSocketServer = require('ws').Server
var wss = new WebSocketServer({ port: 8081 });

wss.on('connection', function connection(ws) {

  ws.on('message', function incoming(message) {
    console.log('received: %s', message);
  });

  ws.send("Hello");
});

wss.broadcast = function broadcast(data) {
  wss.clients.forEach(function each(client) {
    client.send(data);
  });
};