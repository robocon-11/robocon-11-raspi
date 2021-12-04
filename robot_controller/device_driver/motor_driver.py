import pigpio
import time
import core
import logger
from threading import Thread

# Pin Assigns
CW_R = 12
CCW_R = 16
CW_L = 5
CCW_L = 13
OUTPUTS = [CW_R, CCW_R, CW_L, CCW_L]

# 定数
STEP_AMOUNT = 0.018  # 1ステップの角度[deg]
DUTY = 6500  # Duty比
FREQUENCY = 18 * (10 ** 3)  # 周波数[Hz]

_velocity_rate_r = 1.0  # 右モータの速度の倍率（0~1）
_velocity_rate_l = 1.0  # 左モータの速度の倍率（0~1）

# https://www.orientalmotor.co.jp/tech/support_tool/speed/
rps_r = FREQUENCY * _velocity_rate_r * STEP_AMOUNT / 360  # round per sec (右モータ）
rps_l = FREQUENCY * _velocity_rate_l * STEP_AMOUNT / 360  # round per sec (左モータ）

running_r = False  # 右モータが止まっているかどうか
running_l = False  # 左モータが止まっているかどうか

_th_l: Thread  # 右モータ用スレッド
_th_r: Thread  # 左モータ用スレッド

_pi = pigpio.pi()


# https://qiita.com/RyosukeKamei/items/9b15007bf1b77d33764f
def __init__():
    pass


def _th_r_do():
    while core.running:
        if running_r:
            _pi.hardware_PWM(CW_R, int(FREQUENCY * _velocity_rate_r), DUTY)
        else:
            _pi.hardware_PWM(CW_R, 0, DUTY)
        # time.sleep(0.01)


def _th_l_do():
    while core.running:
        if running_l:
            _pi.hardware_PWM(CCW_L, int(FREQUENCY * _velocity_rate_l), DUTY)
        else:
            _pi.hardware_PWM(CCW_L, 0, DUTY)
        # time.sleep(0.01)


def init():
    for pin in OUTPUTS:
        _pi.set_mode(pin, pigpio.OUTPUT)

    global _th_l, _th_r
    _th_r = Thread(target=_th_r_do)
    _th_r.start()
    _th_l = Thread(target=_th_l_do)
    _th_l.start()


def stop():
    for pin in OUTPUTS:
        _pi.set_mode(pin, pigpio.INPUT)
    _pi.stop()


# velocity_rate [deg/s]
def set_velocity_rate_r(velocity_rate: float):
    logger.debug("R: " + str(velocity_rate))
    global _velocity_rate_r
    vr = velocity_rate / (360 * rps_r)
    _velocity_rate_r = vr


# velocity_rate [deg/s]
def set_velocity_rate_l(velocity_rate: float):
    logger.debug("L: " + str(velocity_rate))
    global _velocity_rate_l
    vl = velocity_rate / (360 * rps_r)
    _velocity_rate_l = vl


# TODO 本番では実装しない
def move_forward():
    global running_l, running_r, _velocity_rate_l, _velocity_rate_r
    running_l = True
    running_r = True
    _velocity_rate_l = 1.0
    _velocity_rate_r = 1.0


def move_backward():
    global running_l, running_r, _velocity_rate_l, _velocity_rate_r
    running_l = True
    running_r = True
    _velocity_rate_l = -1.0
    _velocity_rate_r = -1.0


def move_right():
    global running_l, running_r, _velocity_rate_l, _velocity_rate_r
    running_l = True
    running_r = True
    _velocity_rate_l = 0.9
    _velocity_rate_r = 0.6


def move_left():
    global running_l, running_r, _velocity_rate_l, _velocity_rate_r
    running_l = True
    running_r = True
    _velocity_rate_l = 0.6
    _velocity_rate_r = 0.9
