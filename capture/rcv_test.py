import socket
import os
# import os, os.path
# import time

if os.path.exists("/tmp/stream_process"):
    os.remove("/tmp/stream_process")

print("Opening socket...")
server = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
server.bind("/tmp/stream_process")

print("Listening...")
while True:
    datagram = server.recv(4800)

    if not datagram:
        break
    else:
        print("-" * 20)
        print("image received")
        if "DONE" == datagram:
            break
print("-" * 20)
print("Shutting down...")
server.close()
os.remove("/tmp/stream_process")
print("Done")