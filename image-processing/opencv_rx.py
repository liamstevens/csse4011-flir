#!/usr/bin/python -u

import sys, os
import socket, select

import calendar, time

import cv2
import numpy as np

from collections import deque

import flir_process_lib as fpl
import target_lib as tl

epoll = select.epoll()
cascade = cv2.CascadeClassifier("haarcascade_frontalface_default.xml")
epoch = time.time()

socket_buf_size = 1*1024*1024

# GLOBAL CONFIGURABLES
save_file_enable = 0
multiple_faces = 1
colorize = 1
output_view = 3
overlay_pc = 30

flipx = 0
flipy = 1

x_pos  = 40
x_size = 240
y_pos  = 10
y_size = 200

jpg_quality = 95
mkdir = 0
directory = "out_data/"+time.strftime("%Y%m%d-%H%M%S")

# Main operation loop
def main():
    
    picam_ready = 0
    flir_ready = 0

    jpg = []
    pgm = []

    cv2.setNumThreads(3)

    try:

        # Create or connect to all required UDS endpoints
        node_tx = uds_connect("/run/shm/cv2node")

        node_rx = uds_bind("/run/shm/node2cv")

        picam_rx = uds_bind("/run/shm/pi2cv")

        flir_rx = uds_bind("/run/shm/flir2cv")

        # Main function loop
        while True:

            # Wait for one of the UDS sockets to become ready (blocking)
            events = epoll.poll()

            # For each socket that is ready, read in data and save it
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

            # Once we have both a picam and a flir image, move on, else wait a bit longer
            if (picam_ready != 1 or flir_ready != 1):
                continue

            # Decode the picam image (jpg)
            nparr = np.fromstring(jpg, np.uint8)
            pi_cam_img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

            # Decode the flir image (techically a raw 60x80 uint8_t data buffer)
            nparr = np.fromstring(pgm, np.uint8)
            flir_img = np.reshape(nparr, (60, 80))

            # Process them and combine them
            combined_img, detections = do_preprocessing(pi_cam_img, flir_img)

            # Measure heartbeats
            msg = do_measurement(combined_img, detections)

            # Generate the output
            out_img = do_output(combined_img, detections)

            # Send a text message to the web browser, (\x40\x11 as magic number)
            node_tx.send("\x40\x11" +  msg)

            # Send the output image to the web browser
            node_tx.send(out_img)

            # Reset for next round
            picam_ready = 0
            flir_ready = 0

            cv2.waitKey(1)

    except Exception as e:
        print "Exception: " + str(e)

    finally:
        print "Exiting"

# Handle commands and save results in global variables
def handle_cmd(cmd):

    global output_view
    global overlay_pc
    global flipx
    global flipy
    global colorize
    global multiple_faces
    global save_file_enable
    global x_pos
    global x_size
    global y_pos
    global y_size

    print "Got Command: " + cmd

    if (cmd[0] != '!'):
        print "Invalid Format"
        return

    if (cmd[1] == 'V'):
        output_view = int(cmd[2])
        print "Output view is now: " + str(output_view)

    elif (cmd[1] == '%'):
        overlay_pc = int(cmd[2:])
        print "Overlay %% is now: " + str(overlay_pc)

    elif (cmd[1] == 'O'):
        flipx = int(cmd[2])
        print "Flip X is now: " + str(flipx)

    elif (cmd[1] == 'U'):
        flipy = int(cmd[2])
        print "Flip Y is now: " + str(flipy)

    elif (cmd[1] == 'C'):
        colorize = int(cmd[2])
        print "Colorize flir is now: " + str(colorize)

    elif (cmd[1] == 'M'):
        multiple_faces = int(cmd[2])
        print "Multiple faces is now: " + str(multiple_faces)

    elif (cmd[1] == 'S'):
        save_file_enable = int(cmd[2])
        print "Saving is now: " + str(save_file_enable)

    elif (cmd[1] == 'X'):
        x_pos = int(cmd[2:])
        print "XPos is now: " + str(x_pos)

    elif (cmd[1] == 'x'):
        x_size = int(cmd[2:])
        print "XSize is now: " + str(x_size)

    elif (cmd[1] == 'Y'):
        y_pos = int(cmd[2:])
        print "YPos is now: " + str(y_pos)

    elif (cmd[1] == 'y'):
        y_size = int(cmd[2:])
        print "YSize is now: " + str(y_size)


# Helper function to create a UDS endpoint -- Also adds to epoll
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


# Helper function to connect to a UDS endpoint
def uds_connect(path):

    global socket_buf_size

    sock = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF,socket_buf_size)
    sock.connect(path)
    return sock


# Given the two images, JPG in 1, FLIR in 2, combine them as best we can
def do_preprocessing(image1, image2):

    # Calculate the bounding box required to hold both image1 and two, regardless of their size or offset
    points = np.array([[0,0], [image1.shape[0],image1.shape[1]], [y_pos,x_pos], [y_pos+y_size, x_pos+x_size]])
    rect = cv2.boundingRect(points)

    # Create an image to house the two images, based on the dimensions calculated above
    combined_img = np.zeros((rect[2]-1,rect[3]-1,4), np.uint8)

    # Resize and flip flir image as required
    image2 = resize_flir_image(image2)

    # Figure out absolute positioning of image1 (x1,y1) and image2 (x2,y2) based on bounding box
    x1 = 0 if (rect[1] >= 0) else abs(rect[1])
    y1 = 0 if (rect[0] >= 0) else abs(rect[0])
    x2 = 0 if (x_pos < 0) else x_pos
    y2 = 0 if (y_pos < 0) else y_pos

    # Copy jpg data into combined image, channels 0-2.. or does it just make a view?
    combined_img[y1:y1+image1.shape[0],x1:x1+image1.shape[1],0:3] = image1

    # Copy flir data into channel 3
    combined_img[y2:y2+y_size,x2:x2+x_size,3] = image2

    # Run facial detection on the image, seems to only work on channels 0-2, doesnt try on flir data
    detections = fpl.face_cascade(cascade, combined_img, False)

    # TODO: Consider sorting detections or something?

    # Strip all but the first detection if only 1 is requested
    if ((multiple_faces == 0) and (len(detections) > 1)):
        mask = np.zeros(len(detections), dtype=bool)
        mask[[0]] = True
        detections = detections[mask]

    return (combined_img, detections)


# Resize and flip the flir image
def resize_flir_image(image):
    
    if (flipx == 1 and flipy == 1):
        image = cv2.flip(image, -1)
    elif (flipx == 1):
        image = cv2.flip(image, 1)
    elif (flipy == 1):
        image = cv2.flip(image, 0)

    return cv2.resize(image, (x_size, y_size), interpolation = cv2.INTER_CUBIC)


targets = []

# Empty function, will be used for heartbeat measurement
def do_measurement(image, detections):

    global targets

    msg = ""

    targets = [t for t in targets if (t.timer > 0)]

    targets = tl.sort_targets(targets)

    found, not_found = tl.validate_targets(targets, detections)

    for r in found:
        pass

    for r in not_found:
        targets.append(tl.target(r,0))

    fnf = found + not_found

    for idx, t in enumerate(targets): 
        print "Target " + str(idx) + " with ROI: " + str(t.roi) + " updating to " + str(fnf[idx]) 
        t.update_roi(fnf[idx])
        t.update_lum(image[:,:,3])
        t.find_frequency()
        print "Rate: " + str(t.rate) +" (Samples: (" + str(len(t.history)) + ")"
        if (t.rate < 50):
            msg = msg + "User " + str(idx) + " detecting heart rate\r\n"
        else
            msg = msg + "User " + str(idx) + " has heart rate of " + str(t.rate) + "\r\n"
    
    if (len(targets) == 0):
        return "No heartbeats detected"
    else:
        return msg

def do_output(image, detections):

    global jpg_quality
    global mkdir
    global output_view
    global save_file_enable

    # Pre-allocate required storage space for images 
    #   -- Note, all the same size, and IR component is 3 channels for RGB colorization
    result_image  = np.zeros((image.shape[0],image.shape[1],3), np.uint8)
    rgb_component = np.zeros((image.shape[0],image.shape[1],3), np.uint8)
    ir_component  = np.zeros((image.shape[0],image.shape[1],3), np.uint8)

    # Split RGB Channels into rgb_component, and split IR into 3x ir_component channels
    cv2.mixChannels( [image], [rgb_component, ir_component], [0,0, 1,1, 2,2, 3,3, 3,4, 3,5] )

    # If saving requested...
    if (save_file_enable == 1):

        # Get the millisecond timestamp for this frame
        timestamp = int(round((time.time()-epoch)*1000))

        # If output directories haven't yet been made, do it now
        if (mkdir == 0):
            os.makedirs(directory+"/cam/")
            os.makedirs(directory+"/flir/")
            mkdir = 1

        # Write RGB to file
        cv2.imwrite(directory+"/cam/"+str(timestamp)+".jpg", rgb_component)
        # Write IR to file, jpg for file size?
        cv2.imwrite(directory+"/flir/"+str(timestamp)+".jpg", ir_component)

    # If colorizing requested
    if (colorize == 1):
        ir_component = cv2.LUT(ir_component, LUT)   # For each pixel, replace with value from LUT

    # Based on user preference, set result_image
    if (output_view == 2):
        result_image = rgb_component
    elif (output_view == 1):
        result_image = ir_component
    elif (output_view == 0):
        # No Video, leave result image as all black
        pass
    else:
        # If combined, addWeighted as user preference
        result_image = cv2.addWeighted(rgb_component, ((100-overlay_pc)/100.0), ir_component, (overlay_pc/100.0),  0)

    # If no output view, don't bother drawing the detections
    if (output_view != 0):
        fpl.detections_draw(result_image, detections)

    # Browser expects the image to be 320x240, so scale it down now
    result_image = cv2.resize(result_image, (320, 240), interpolation = cv2.INTER_CUBIC)
    out_img = cv2.imencode('.jpeg', result_image,  [int(cv2.IMWRITE_JPEG_QUALITY), jpg_quality])[1].tostring()

    # Node UDS implementation can only acces up to 64kB, so try and compress Jpg to sit around 58kB
    if (len(out_img) > 58000):
        if (jpg_quality > 0):
            jpg_quality = jpg_quality - 1
    else:
        if (jpg_quality < 98):
            jpg_quality = jpg_quality + 1

    return out_img

# Brane's Heatmap, converted into an np.array, and reshaped to the correct format for the LUT function
LUT = [0,0,0,16,0,0,33,0,0,42,0,0,49,0,0,56,0,0,63,0,0,70,0,0,77,0,0,83,0,0,87,0,1,91,0,2,95,0,3,99,0,4,103,0,5,106,0,7,110,0,9,115,0,11,116,0,12,118,0,13,120,0,16,122,0,19,124,0,22,127,0,25,129,0,28,131,0,31,133,0,34,135,0,38,137,0,42,138,0,45,140,0,48,141,0,52,143,0,55,144,0,58,146,0,61,147,0,63,148,0,65,149,0,68,149,0,71,150,0,74,150,0,76,151,0,79,151,0,82,152,0,85,152,0,88,153,0,92,154,0,94,155,0,97,155,0,101,155,0,104,155,0,107,156,0,110,156,0,112,156,0,114,157,0,117,157,0,121,157,0,124,157,0,126,157,0,129,157,0,132,157,0,135,157,0,137,156,0,140,156,0,143,155,0,146,155,0,149,155,0,152,155,0,154,155,0,157,155,0,159,155,0,161,154,0,164,154,0,166,153,0,168,153,0,170,152,0,172,152,0,174,151,1,175,151,1,177,150,1,178,149,1,180,149,2,182,149,3,183,148,4,185,147,4,186,147,5,188,146,5,189,146,5,190,145,6,191,144,7,192,143,9,193,142,10,194,141,11,195,139,12,197,138,13,198,136,15,200,134,17,201,133,18,202,131,20,203,129,21,204,126,23,206,123,24,207,121,26,208,118,27,208,116,28,209,113,30,210,111,32,211,108,34,212,104,36,213,101,38,214,98,40,216,95,42,217,91,44,218,87,46,219,81,47,220,76,49,221,70,51,222,65,53,223,59,54,223,54,56,224,48,57,224,42,59,225,37,61,226,31,63,227,28,65,228,25,67,228,23,69,229,21,71,230,19,72,231,17,74,231,15,76,232,13,77,233,11,78,234,10,80,234,9,82,235,8,84,235,8,86,236,7,87,236,7,89,236,6,91,237,5,92,237,4,94,238,4,95,238,3,97,239,3,99,239,3,100,240,3,102,240,2,103,241,2,104,241,1,106,241,1,107,241,1,109,242,1,111,242,1,113,243,0,114,243,0,115,243,0,117,244,0,119,244,0,121,244,0,124,244,0,126,245,0,128,245,0,129,246,0,131,246,0,133,247,0,134,247,0,136,248,0,137,248,0,139,248,0,140,248,0,142,249,0,143,249,0,144,249,0,146,249,0,148,249,0,150,250,0,153,250,0,155,251,0,157,251,0,159,252,0,161,252,0,163,253,0,166,253,0,168,253,0,170,253,0,172,253,0,174,253,0,176,254,0,177,254,0,178,254,0,181,254,0,183,254,0,185,254,0,186,254,0,188,254,0,190,254,0,191,254,0,193,254,0,195,254,0,197,254,0,199,254,0,200,254,1,202,254,1,203,254,2,205,254,3,206,254,4,207,254,6,209,254,8,211,254,10,213,254,11,215,254,12,216,254,14,218,254,16,219,255,20,220,255,24,221,255,28,222,255,32,224,255,36,225,255,39,227,255,44,228,255,50,229,255,56,230,255,62,231,255,67,233,255,73,234,255,79,236,255,85,237,255,92,238,255,98,238,255,105,239,255,111,240,255,119,241,255,127,241,255,135,242,255,142,243,255,149,244,255,156,244,255,164,245,255,171,245,255,178,246,255,184,247,255,190,247,255,195,248,255,201,248,255,206,249,255,212,250,255,218,251,255,224,252,255,229,253,255,235,253,255,240,254,255,244,254,255,249,255,255,252,255,255,255,255,255]
LUT = np.array(LUT, np.uint8)
LUT = np.reshape(LUT, (256, 1, 3))

if __name__ == "__main__":
    sys.exit(main())
