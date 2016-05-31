#!/usr/bin/python

import sys, os
import socket


def main():

    parent, child = socket.socketpair()

    pid = os.fork()

    if pid:
        print 'in parent, sending message'
        child.close()
        parent.sendall('ping')
        response = parent.recv(1024)
        print 'response from child:', response
        parent.close()

    else:
        print 'in child, waiting for message'
        parent.close()
        message = child.recv(1024)
        print 'message from parent:', message
        child.sendall('pong')
        child.close()


if __name__ == "__main__":

    sys.exit(main())


# Increase Buffer sizes?
# https://www.raspberrypi.org/forums/viewtopic.php?f=81&t=106052