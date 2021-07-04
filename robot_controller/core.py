from gpiozero import LED
from time import sleep, time

# For example
led = LED(17)
while True:
    led.on()
    sleep(0.5)
    led.off()
    sleep(0.5)