import sys, cv2

def face_cascade(cascade, image, gflag=True):
    if not gflag:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image
    return cascade.detectMultiScale(gray, scaleFactor = 1.5, minNeighbors = 5, minSize = (30, 30), flags = cv2.CASCADE_SCALE_IMAGE)


def detections_draw(image, detections):
    for (x, y, w, h) in detections:
        print "({0}, {1}, {2}, {3})".format(x, y, w, h)
        cv2.rectangle(image, (x, y), (x + w, y + h), (0, 0, 255), 2)

def main(argv = None):
    if argv is None:
        argv = sys.argv

    cap = cv2.VideoCapture(0)
    cascade_path = sys.argv[1]
    image_path = sys.argv[2]
    result_path = sys.argv[3] if len(sys.argv) > 3 else None
    cascade = cv2.CascadeClassifier(cascade_path)
    #For webcam capture
    if image_path == 'cam':
        while(True):
            ret, image = cap.read()
        #image = cv2.imread(image_path)
            if image is None:
                print "ERROR: Image did not load."
                return 2

            detections = face_cascade(cascade, image, False)

            print "Found {0} objects!".format(len(detections))
            if result_path is None:
                detections_draw(image, detections)
                cv2.imshow("Objects found", image)
                cv2.waitKey(1)
            else:
                cv2.imshow("No objects found", image)
                cv2.waitKey(1)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                break;
#          cv2.imwrite(result_path, image)
        cap.release()
        cv2.destroyAllWindows()
    else:
        image = cv2.imread(image_path)
        
        detections = face_cascade(cascade, image)
        if result_path is None:
            detections_draw(image, detections)
            cv2.imshow("Objects found", image)
            cv2.waitKey(0)
        else:
            cv2.imshow("No objects found", image)
            cv2.waitKey(0)

if __name__ == "__main__":
    sys.exit(main())
