import threading
import time
import core
import logger
from gpiozero import LED, Button
from device_driver import motor_driver


PIN_LED_BLUE = 26
PIN_LED_GREEN = 21
PIN_LED_RED = 20
PIN_LED_YELLOW = 6
PIN_BUTTON_START = 23
PIN_BUTTON_STOP = 24
PIN_RESET = 4


_blue = LED(PIN_LED_BLUE)
_blue_led = False

_green = LED(PIN_LED_GREEN)
_green_led = False

_red = LED(PIN_LED_RED)
_red_led = False

_yellow = LED(PIN_LED_YELLOW)
_yellow_led = False

start_button = Button(PIN_BUTTON_START)
stop_button = Button(PIN_BUTTON_STOP)
button_was_held = False


def init():
    start_button.when_held = _on_button_held
    start_button.when_deactivated = _on_button_released
    stop_button.when_held = _on_button_held
    stop_button.when_deactivated = _on_button_released

    red_led_on()
    logger.info("Loaded modules. Process is ready.")

    while not core.running:
        pass


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


def red_led_off():
    global _red
    _red.off()


def yellow_led_on():
    global _yellow
    _yellow.on()


def _on_button_held():
    global button_was_held
    button_was_held = True


def _on_button_released(button: Button):
    global button_was_held
    if not button_was_held:
        if button.pin.number == PIN_BUTTON_START:
            logger.info("Process Started.")
            core.running = True
            core.instance = core.Core()

            with LED(PIN_RESET) as reset_pin:
                reset_pin.on()
                time.sleep(0.2)
                reset_pin.off()

            threading.Thread(target=_led_scheduler).start()

        elif button.pin.number == PIN_BUTTON_STOP:
            logger.critical("Process is stopped by the controller.")
            motor_driver.stop()
            exit(0)
    button_was_held = False
