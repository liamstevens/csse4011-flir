#!/usr/bin/python

import io
import socket
import time

import picamera

w_res = 320
h_res = 240
fps = 30

frame_divider = 0

try:

    sock = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 1*1024*1024)
    sock.connect("/run/shm/pi2cv")

    with picamera.PiCamera() as camera:

        camera.resolution = (w_res, h_res)
        camera.framerate = fps

        print "Started with framerate: " + str(camera._get_framerate())
        print "Started with resolution: " + str(camera._get_resolution())

        time.sleep(2)

        stream = io.BytesIO()

        for foo in camera.capture_continuous(stream, 'jpeg', use_video_port=True):
            if (frame_divider == 0):
                sock.send(stream.getvalue())
            stream.seek(0)
            stream.truncate()
            frame_divider = (frame_divider+1)%3

except Exception as e:
    print "Exception: " + str(e)
