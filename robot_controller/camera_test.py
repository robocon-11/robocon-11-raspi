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
cam = cv2.VideoCapture(0, cv2.CAP_MSMF)
cam.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc('M', 'J', 'P', 'G'))
cam.set(cv2.CAP_PROP_FPS, 20)            # カメラFPSを60FPSに設定
cam.set(cv2.CAP_PROP_FRAME_WIDTH, 200)   # カメラ画像の横幅を1280に設定
cam.set(cv2.CAP_PROP_FRAME_HEIGHT, 113)  # カメラ画像の縦幅を720に設定

queue = []
while True:
    ret, frame = cam.read()
    gray = cv2.filter2D(cv2.medianBlur(cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY), ksize=5), -1, make_sharp_kernel(1))
    """
    custom_cascade = cv2.CascadeClassifier('soccerball_classifier.xml')

    custom_rect = custom_cascade.detectMultiScale(gray, scaleFactor=1.3, minNeighbors=10, minSize=(100, 100))
    circles = cv2.HoughCircles(gray, cv2.HOUGH_GRADIENT, dp=1, minDist=20, param1=100, param2=60, minRadius=0, maxRadius=0)
    if circles is None or len(circles) == 0:
        continue

    circle = circles[0][0]

    if len(custom_rect) > 0:
        for rect in custom_rect:
            x_av = (rect[0] + rect[2]) / 2
            y_av = (rect[1] + rect[3]) / 2
            if np.sqrt((x_av - circle[0]) ** 2 + (y_av - circle[1]) ** 2) < circle[2]:
                cv2.rectangle(frame, tuple(rect[0:2]), tuple(rect[0:2]+rect[2:4]), (0, 0, 255), thickness=3)

    cv2.imshow('image', frame)

    """
    circles = cv2.HoughCircles(gray, cv2.HOUGH_GRADIENT, dp=0.8, minDist=20, param1=100, param2=45, minRadius=15, maxRadius=0)

    if circles is not None and len(circles) > 0:
        if len(queue) > 3:
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

        img1 = cv2.circle(gray, center=(int(x_sum / len(queue)), int(y_sum / len(queue))), radius=int(radius_sum / len(queue)), color=(0, 0, 255), thickness=3)
        cv2.imshow('frame', img1)
    else:
        cv2.imshow('frame', gray)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cam.release()
cv2.destroyAllWindows()

