#!/usr/bin/python -u

import sys, os
import socket, select

import calendar, time

import cv2
import numpy as np

import face_test as ft

# combined_img = np.zeros((480,640,3), np.uint8)
# pi_cam_img = np.zeros((480,640,3), np.uint8)
# flir_img = np.zeros((60,80,1), np.uint8)

epoll = select.epoll()
cascade = cv2.CascadeClassifier("haarcascade_frontalface_default.xml")

socket_buf_size = 0

def main():

    jpg_quality = 95
    picam_ready = 0
    flir_ready = 0

    jpg = []
    pgm = []

    cv2.setNumThreads(0)

    try:

        node_tx = uds_connect("/run/shm/cv2node")

        node_rx = uds_bind("/run/shm/node2cv")

        picam_rx = uds_bind("/run/shm/pi2cv")

        flir_rx = uds_bind("/run/shm/flir2cv")

        while True:

            events = epoll.poll()

            for fileno, event in events:

                if (picam_rx.fileno() == fileno):
                    jpg = picam_rx.recv(socket_buf_size)
                    picam_ready = 1

                if (flir_rx.fileno() == fileno):
                    pgm = flir_rx.recv(socket_buf_size)
                    print "GOT: " + str(len(pgm))
                    flir_ready = 1

                if (node_rx.fileno() == fileno):
                    cmd = node_rx.recv(socket_buf_size)
                    #handle command here

            if (picam_ready != 1 or flir_ready != 1):
                continue

            nparr = np.fromstring(jpg, np.uint8)
            pi_cam_img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

            nparr = np.fromstring(pgm, np.uint8)
            flir_img = np.reshape(nparr, (60, 80))

            combined_img = do_stuff(pi_cam_img, flir_img)

            jpg = cv2.imencode('.jpeg', combined_img,  [int(cv2.IMWRITE_JPEG_QUALITY), jpg_quality])[1].tostring()
            node_tx.send(jpg)

            if (len(jpg) > 58000):
                if (jpg_quality > 0):
                    jpg_quality = jpg_quality - 1
            else:
                if (jpg_quality < 95):
                    jpg_quality = jpg_quality + 1

            picam_ready = 0
            flir_ready = 0

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

    except Exception as e:
        print "Exception: " + str(e)

    finally:
        print "Exiting"

def uds_bind(path):

    global epoll
    global socket_buf_size

    if os.path.exists( path ):
        os.remove( path )

    sock = socket.socket( socket.AF_UNIX, socket.SOCK_DGRAM )
    sock.bind(path)
    sock.setblocking(0)
    epoll.register(sock.fileno(), select.EPOLLIN)

    if (socket_buf_size == 0):
        socket_buf_size = sock.getsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF)

    return sock

def uds_connect(path):

    sock = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
    sock.connect(path)
    return sock

def do_stuff(image1, image2):

    detections = ft.face_cascade(cascade, image1, False)
    ft.detections_draw(image1, detections)

    cv2.putText(image1, str(calendar.timegm(time.gmtime())), (420,40), cv2.FONT_HERSHEY_SIMPLEX, 1,(0,0,0),2,cv2.LINE_AA)

    # image_out[:,:,0:3] = image1[:,:,:]
    # image_out[0:60,0:80,4] = image2[0:60,0:80]

    image1[0:60,0:80,0] = image2[0:60,0:80]
    image1[0:60,0:80,1] = image2[0:60,0:80]
    image1[0:60,0:80,2] = image2[0:60,0:80]

    # cv2.imshow( "Stuff Done", image1 )

    return image1

if __name__ == "__main__":

    sys.exit(main())


# Increase Buffer sizes?
# https://www.raspberrypi.org/forums/viewtopic.php?f=81&t=106052
