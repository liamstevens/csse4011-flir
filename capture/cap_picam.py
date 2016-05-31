#!/usr/bin/python

import io
import socket
import time

import picamera

w_res = 640
h_res = 480
fps = 10

print picamera

try:

    sock = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 1*1024*1024)
    sock.connect("/run/shm/pi2cv")

    with picamera.PiCamera() as camera:

        camera.resolution = (w_res, h_res)
        camera.framerate = fps

        time.sleep(2)

        stream = io.BytesIO()

        for foo in camera.capture_continuous(stream, 'jpeg', use_video_port=True):
            sock.send(stream.getvalue())
            stream.seek(0)
            stream.truncate()

except Exception as e:
    print "Exception: " + str(e)
