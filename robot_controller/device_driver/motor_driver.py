from connection.interface.internal_interface import *
import RPi.GPIO as GPIO

cw_r = 5
ccw_r = 6
cw_l = 13
ccw_l = 19
outputs = [cw_r,ccw_r,cw_l,ccw_l]

def __init__():
    GPIO.setmode(GPIO.BCM)
    for output in outputs:
        GPIO.setup(output,GPIO.OUT, initial=GPIO.LOW)

def move_forward():
    pass 

def move_backward():
    pass

def move_right():
    pass

def move_left():
    pass