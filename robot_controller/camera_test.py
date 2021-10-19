from time import sleep
import cv2
import numpy as np


def make_sharp_kernel(k: int):
    return np.array([
        [-k / 9, -k / 9, -k / 9],
        [-k / 9, 1 + 8 * k / 9, k / 9],
        [-k / 9, -k / 9, -k / 9]
    ], np.float32)


# Test for Raspberry Pi Camera
cam = cv2.VideoCapture(0)
queue = []
while True:
    ret, frame = cam.read()
    gray = cv2.filter2D(cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY), -1, make_sharp_kernel(1))
    circles = cv2.HoughCircles(gray, cv2.HOUGH_GRADIENT, dp=1, minDist=20, param1=100, param2=60, minRadius=0, maxRadius=0)

    if circles is not None and len(circles) > 0:
        if len(queue) > 5:
            queue.pop()
        queue.insert(0, circles[0][0])
        img = cv2.cvtColor(gray, cv2.COLOR_GRAY2RGB)

        x_sum = 0.0
        y_sum = 0.0
        radius_sum = 0.0

        for array in queue:
            x_sum += array[0]
            y_sum += array[1]
            radius_sum += array[2]

        img1 = cv2.circle(img, center=(int(x_sum / len(queue)), int(y_sum / len(queue))), radius=int(radius_sum / len(queue)), color=(0, 0, 255))
        cv2.imshow('frame', img1)
    else:
        cv2.imshow('frame', gray)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cam.release()
cv2.destroyAllWindows()

