#!/bin/bash

MODE="PI"
if [ "$#" -gt 0 ]; then
	MODE="$1"
fi

NODE_PATH="web"
NODE_FILE="main.js"

CV_PATH="image-processing"
CV_FILE="opencv_rx.py"

if [ $MODE = "USB" ]; then
	echo "Starting in USB mode"
	CAP_PATH="scripts"
	PICAM_FILE="mock_picamera_usb.py" 
	FLIR_FILE="pgm_noise.py"
elif [ $MODE = "STATIC" ]; then
	echo "Starting in STATIC mode"
	CAP_PATH="scripts"
	PICAM_FILE="mock_picamera_static.py"
	FLIR_FILE="mock_flir_static.py"
else
	echo "Starting in PI mode"
	CAP_PATH="capture"
	PICAM_FILE="picamera.py"
	FLIR_FILE="lepton"
fi

# Run the Node Server
cd $NODE_PATH
node $NODE_FILE > node.log 2>&1 &
NODE_PID=$!
cd ..

sleep 1
if kill -0 "$NODE_PID" >/dev/null 2>&1 ; then
	echo "Node Server Started OK"

	# Run the openCV Script
	cd $CV_PATH
	./$CV_FILE > opencv.log 2>&1 &
	OPENCV_PID=$!
	cd ..

	sleep 1
	if kill -0 "$OPENCV_PID" >/dev/null 2>&1 ; then
		echo "OpenCV Script Started OK"

		# Run the PiCam
		cd $CAP_PATH
		./$PICAM_FILE > picam.log 2>&1 &
		PICAM_PID=$!
		cd ..

		sleep 1
		if kill -0 "$PICAM_PID" >/dev/null 2>&1 ; then
			echo "Pi Camera Started OK"

			# Run the FLIR
			cd $CAP_PATH
			./$FLIR_FILE > flir.log 2>&1 &
			FLIR_PID=$!
			cd ..

			sleep 1
			if kill -0 "$FLIR_PID" >/dev/null 2>&1 ; then
				echo "FLIR Camera Started OK"

				read -p "Press any key to exit..."

				# Stop the FLIR
				kill $FLIR_PID
			else 
				echo "FLIR Camera Failed to start"
			fi

			# Stop the PiCam
			kill $PICAM_PID

		else 
			echo "Pi Camera Failed to start"
		fi
		
		# Stop the openCV script
		kill $OPENCV_PID

	else 
		echo "OpenCV Script Failed to start"
	fi
	
	# Stop the Node Server
	kill $NODE_PID

else 
	echo "Node Server Failed to start"
fi
