import threading
import time
import core
from gpiozero import LED, Button


_blue = LED(26)
_blue_led = False

_green = LED(19)
_green_led = False

_red = LED(13)
_red_led = False

start_button = Button(6)


def init():
    if core.running:
        _red.on()
    threading.Thread(target=_led_scheduler).start()


def _led_scheduler():
    global _blue_led
    global _green_led
    while core.running:
        if _blue_led:
            _blue.on()
            time.sleep(0.2)
            _blue.off()
            _blue_led = False
        if _green_led:
            _green.on()
            time.sleep(0.2)
            _green.off()
            _green_led = False


def blue_led_on():
    global _blue_led
    _blue_led = True


def green_led_on():
    global _green_led
    _green_led = True


def red_led_on():
    global _red
    _red.on()
