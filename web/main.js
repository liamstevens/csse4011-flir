
var express = require('express');
var app = express();
var net = require('net');
var fs = require('fs');
var unix = require('unix-dgram');

path = "/run/shm/cv2node"

app.use(express.static('public'));

app.listen(8080, function () {
  console.log('Example app listening on port 8080!');
});

try { 
  fs.unlinkSync(path);
  fs.unlinkSync(path);
} catch (ex) { }

var server = unix.createSocket('unix_dgram');

server.on('message', (msg) => {
  // console.log(`server got msg`);

  wss.broadcast(msg);
});

server.on('error', function(e) {
  console.log(`server got err: ${e}`);
});

server.bind(path);


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