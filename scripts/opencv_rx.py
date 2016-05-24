#!/usr/bin/python
import sys, os
import socket, select

import calendar, time

import cv2
import numpy as np

combined_img = np.zeros((480,640,4), np.uint8)

picam_ready = 0
flir_ready = 0

try:

    epoll = select.epoll()

    nodejs_o = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
    nodejs_o.connect("/run/shm/cv2node")


    if os.path.exists( "/run/shm/node2cv" ):
        os.remove( "/run/shm/node2cv" )
    
    nodejs_i = socket.socket( socket.AF_UNIX, socket.SOCK_DGRAM )
    nodejs_i.bind("/run/shm/node2cv")
    nodejs_i.setblocking(0)
    epoll.register(nodejs_i.fileno(), select.EPOLLIN)


    if os.path.exists( "/run/shm/pi2cv" ):
        os.remove( "/run/shm/pi2cv" )
    
    picam = socket.socket( socket.AF_UNIX, socket.SOCK_DGRAM )
    picam.bind("/run/shm/pi2cv")
    picam.setblocking(0)
    epoll.register(picam.fileno(), select.EPOLLIN)

    if os.path.exists( "/run/shm/flir2cv" ):
        os.remove( "/run/shm/flir2cv" )

    flir = socket.socket( socket.AF_UNIX, socket.SOCK_DGRAM )
    flir.bind("/run/shm/flir2cv")
    flir.setblocking(0)
    epoll.register(flir.fileno(), select.EPOLLIN)

    while True:

        events = epoll.poll()

        for fileno, event in events:

            if (picam.fileno() == fileno):
                jpg = picam.recv(262144)
                nparr = np.fromstring(jpg, np.uint8)
                pi_cam_img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
                # cv2.imshow( "PiCam", pi_cam_img );

                combined_img[:,:,0:3] = pi_cam_img

                picam_ready = 1

            if (flir.fileno() == fileno):
                ir = flir.recv(262144)
                nparr = np.fromstring(ir, np.uint8)
                flir_img = cv2.imdecode(nparr, cv2.IMREAD_UNCHANGED)
                # cv2.imshow( "FLIR", flir_img );

                combined_img[0:60,0:80,3] = flir_img

                flir_ready = 1

            if (nodejs_i.fileno() == fileno):
                cmd = nodejs_i.recv(262144)
                #handle command here

        if (picam_ready != 1 or flir_ready != 1):
            continue

        combined_img[0:60,0:80,0] = combined_img[0:60,0:80,3]
        combined_img[0:60,0:80,1] = combined_img[0:60,0:80,3]
        combined_img[0:60,0:80,2] = combined_img[0:60,0:80,3]

        cv2.putText(combined_img, str(calendar.timegm(time.gmtime())), (420,40), cv2.FONT_HERSHEY_SIMPLEX, 1,(0,0,0),2,cv2.LINE_AA)

        cv2.imshow( "combined_img", combined_img ); 

        jpg = cv2.imencode('.jpeg', combined_img)[1].tostring()
        nodejs_o.send(jpg)

        picam_ready = 0
        flir_ready = 0

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

except Exception as e:
    print "Exception: " + str(e)

finally:
    print "Exiting"