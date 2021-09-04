from gpiozero import LED
from time import sleep
import cv2


# Test for Raspberry Pi Camera
cam = cv2.VideoCapture(0)
while True:
    ret, frame = cam.read()
    cv2.imshow('frame', frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cam.release()
cv2.destroyAllWindows()

# For example
led = LED(17)
while True:
    led.on()
    sleep(0.5)
    led.off()
    sleep(0.5)

