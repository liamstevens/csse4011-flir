#!/usr/bin/python -u

import sys, os
import socket, select

import calendar, time

import cv2
import numpy as np

import face_test as ft

# 
# pi_cam_img = np.zeros((480,640,3), np.uint8)
# flir_img = np.zeros((60,80,1), np.uint8)

epoll = select.epoll()
cascade = cv2.CascadeClassifier("haarcascade_frontalface_default.xml")

socket_buf_size = 1*1024*1024

# GLOBAL CONFIGURABLES
save_file_enable = True

def main():
    
    picam_ready = 0
    flir_ready = 0

    jpg = []
    pgm = []

    cv2.setNumThreads(3)

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
                    flir_ready = 1

                if (node_rx.fileno() == fileno):
                    cmd = node_rx.recv(socket_buf_size)
                    handle_cmd(cmd)

            if (picam_ready != 1 or flir_ready != 1):
                continue

            nparr = np.fromstring(jpg, np.uint8)
            pi_cam_img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

            nparr = np.fromstring(pgm, np.uint8)
            flir_img = np.reshape(nparr, (60, 80))

            combined_img, detections = do_processing(pi_cam_img, flir_img)
            out_img = do_output(combined_img, detections)

            node_tx.send(out_img)

            picam_ready = 0
            flir_ready = 0

    except Exception as e:
        print "Exception: " + str(e)

    finally:
        print "Exiting"

def handle_cmd(cmd):
    print "Got Command: " + cmd

def uds_bind(path):

    global epoll
    global socket_buf_size

    if os.path.exists( path ):
        os.remove( path )

    sock = socket.socket( socket.AF_UNIX, socket.SOCK_DGRAM )
    sock.bind(path)
    sock.setblocking(0)
    epoll.register(sock.fileno(), select.EPOLLIN)

    return sock

def uds_connect(path):

    global socket_buf_size

    sock = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF,socket_buf_size)
    sock.connect(path)
    return sock


def do_processing(image1, image2):

    # TODO: Crop image1 to smaller size to match 

    combined_img = np.zeros((image1.shape[0],image1.shape[1],4), np.uint8)

    # cv2.mixChannels( [image1, image2], [combined_img], [0,0, 1,1, 2,2, 3,3] )
    combined_img[:,:,0:3] = image1
    combined_img[0:60,0:80,3] = image2

    detections = ft.face_cascade(cascade, combined_img, False)

    return (combined_img, detections)

jpg_quality = 95
frame = -1
directory = "out_data/"+time.strftime("%Y%m%d-%H%M%S")
def do_output(image, detections):

    global jpg_quality
    global frame

    result_image = np.zeros((image.shape[0],image.shape[1],3), np.uint8)

    rgb_component = np.zeros((image.shape[0],image.shape[1],3), np.uint8)
    ir_component = np.zeros((image.shape[0],image.shape[1],1), np.uint8)

    cv2.mixChannels( [image], [rgb_component, ir_component], [0,0, 1,1, 2,2, 3,3] )

    frame = frame + 1

    if (save_file_enable == True):

        if (frame == 0):
            os.makedirs(directory+"/cam/")
            os.makedirs(directory+"/flir/")

        # Write image1 to file
        cv2.imwrite(directory+"/cam/"+str(frame)+".jpg", rgb_component)
        # Write image2 to file
        cv2.imwrite(directory+"/flir/"+str(frame)+".pgm", ir_component)

    # Do transformation on incoming image

    result_image = rgb_component

    ft.detections_draw(result_image, detections)

    cv2.putText(result_image, str(calendar.timegm(time.gmtime())), (210,20), cv2.FONT_HERSHEY_SIMPLEX, .5,(0,0,0),1,cv2.LINE_AA)

    out_img = cv2.imencode('.jpeg', result_image,  [int(cv2.IMWRITE_JPEG_QUALITY), jpg_quality])[1].tostring()

    if (len(out_img) > 58000):
        if (jpg_quality > 0):
            jpg_quality = jpg_quality - 1
    else:
        if (jpg_quality < 95):
            jpg_quality = jpg_quality + 1

    return out_img

if __name__ == "__main__":

    sys.exit(main())


# Increase Buffer sizes?
# https://www.raspberrypi.org/forums/viewtopic.php?f=81&t=106052
