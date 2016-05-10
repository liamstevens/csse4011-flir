#!/usr/bin/python

import socket

from random import randint
from time import sleep


def write_to_file(data):
	with open('test.pgm', 'w') as f: 
		f.write(pgm_data)

def write_to_socket(data):
	sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
	sock.sendto(data, ("127.0.0.1", 41234))

if __name__ == "__main__":

	width = 80
	height = 60
	max_val = 0
	freq = 10

	try:
		while True:
			
			data  = []

			for h in range(height):
				
				data.append([])

				for w in range(width):
				
					this_val = randint(0,65535)
					if (this_val > max_val):
						max_val = this_val

					data[h].append(this_val)


			pgm_data = ""
			pgm_data += "P2\n"  								# magic number
			pgm_data += str(width) + " " + str(height) + "\n"  	# dimensions (w x h)
			pgm_data += str(max_val) + "\n"

			for h in range(height):
				
				for w in range(width):

					pgm_data += str(data[h][w]) + " "

				pgm_data += '\n'


			#write_to_file(pgm_data)
			write_to_socket(pgm_data)

			sleep(1.0/freq)

	except:
		print "Exiting"
