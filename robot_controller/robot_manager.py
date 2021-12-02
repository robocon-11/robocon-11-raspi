import math
import threading
import time
import logger
import core
from device_driver import motor_driver
from connection.input_packets import *
from connection.output_packets import *
from connection import connection_manager
from sensor.sensor_mamager import SensorManager

# ステート
STATE_READY = 0
STATE_STARTED = 1
STATE_EXCEEDED_SB_LINE = 2
STATE_EXCEEDED_HALF_LINE = 3

# 移動モード
MODE_STRAIGHT = 0
MODE_PURE_PURSUIT = 1

# 定数
TIRE_RADIUS = 45.0  # タイヤ半径[mm]
TIRE_DISTANCE = 175.0  # タイヤ同士の距離[mm]
ROTATION_DEGREE = 90.0  # 回転時にタイヤが回る角度[deg]
MAX_ANGULAR_VELOCITY = motor_driver.FREQUENCY * motor_driver.STEP_AMOUNT  # タイヤの最大角速度[deg/s] 14400
INTERVAL = 0.5  # 計測間隔[s] 0.05
CORN_WIDTH = 380  # カラーコーンの一辺の長さ[mm]

# 自己位置推定（ステージの左上が基準点）
x = 1100.0  # 自己位置x[mm]
y = 840.0  # 自己位置y[mm]
a_v_l = MAX_ANGULAR_VELOCITY  # 左車輪角速度[deg/s]
a_v_r = MAX_ANGULAR_VELOCITY  # 右車輪角速度[deg/s]
v_l = 0.0  # 左車輪の設置点での速度[mm/s]
v_r = 0.0  # 右車輪の設置点での速度[mm/s]
v = 0.0  # 車速[mm/s]
w = 0.0  # 旋回角速度（両車輪の中点）[deg/s]
p = 0.0  # 旋回半径[mm]
rot = 90.0  # ロボットのx軸に対する角度[deg]

# 仮想ネズミの座標
mouse_x = 1100.0
mouse_y = 1050.0
mouse_v = 2 * math.pi * TIRE_RADIUS * MAX_ANGULAR_VELOCITY / 360  # (=240.21mm/s)
mouse_rot = 0.0  # 仮想ネズミのx軸に対する角度 [deg]
delta = 150  # 仮想ネズミとロボットの間隔 [mm]
stopped = False  # 仮想ネズミが停止中かどうか

# 状態
state = STATE_READY  # 現在の処理段階
mode = MODE_PURE_PURSUIT
direction = 0.0  # degree
line_passed_count = 0
should_update_line = True  # ラインをまたいだことを更新すべきかどうか
last_line_traced_at = 0
measuring_distance = False  # 距離を計測中かどうか
measuring_line_tracer = False  # ライントレーサを計測中かどうか
measuring_nine_axis = False  # 9軸センサで計測中かどうか

_unique_id = 0  # パケットID


def start():
    motor_driver.init()
    threading.Thread(target=_heart_beat).start()
    motor_driver.running_r = True
    motor_driver.running_l = True


# センサを計測する
def measure(method, callback):
    thread = threading.Thread(target=method, args=(callback,))
    thread.start()


# 壁との距離を計測し、実行結果をmethodに返す
def measure_distance(method):
    global measuring_distance
    measuring_distance = True
    while measuring_distance:
        SensorManager() \
            .set_packet(MeasureDistancePacket(unique_id())) \
            .send() \
            .set_on_receive(lambda pk: method(pk))
        time.sleep(1)  # 計測間隔


# ライントレーサの値を計測し、実行結果をmethodに返す
def measure_line_tracer(method):
    global measuring_line_tracer
    measuring_line_tracer = True
    while measuring_line_tracer:
        SensorManager() \
            .set_packet(MeasureLineTracerPacket(unique_id())) \
            .send() \
            .set_on_receive(lambda pk: method(pk))
        time.sleep(1)  # 計測間隔


# ライントレーサの値を計測し、実行結果をmethodに返す
def measure_nine_axis(method):
    global measuring_nine_axis
    measuring_nine_axis = True
    while measuring_nine_axis:
        SensorManager() \
            .set_packet(MeasureNineAxisSensorPacket(unique_id())) \
            .send() \
            .set_on_receive(lambda pk: method(pk))
        time.sleep(1)  # 計測間隔


def stop_measuring_distance():
    global measuring_distance
    measuring_distance = False


def stop_measuring_line_tracer():
    global measuring_line_tracer
    measuring_line_tracer = False


def stop_measuring_nine_axis():
    global measuring_nine_axis
    measuring_nine_axis = False


# ランダムなパケットIDを生成
def unique_id():
    global _unique_id
    result = _unique_id
    _unique_id += 1
    return result


# ライン状態の更新
def update_state():
    if should_update_line:
        global state, line_passed_count
        if state == STATE_READY:
            state = STATE_STARTED
        elif state == STATE_STARTED:
            state = STATE_EXCEEDED_SB_LINE
        elif state == STATE_EXCEEDED_SB_LINE:
            state = STATE_EXCEEDED_HALF_LINE
        elif state == STATE_EXCEEDED_HALF_LINE:
            state = STATE_EXCEEDED_SB_LINE
        line_passed_count += 1


# ライントレースが完了したときのコールバック関数
def on_line_traced(pk: LineTracerResultPacket):
    global last_line_traced_at
    if time.time() - last_line_traced_at > 1.5 and pk.is_on_line:
        update_state()
        last_line_traced_at = time.time()


def on_sensor_data_resulted(pk: SensorDataPacket):
    global line_passed_count, last_line_traced_at
    if pk.line_tracer == 1 and time.time() - last_line_traced_at > 1.5:
        line_passed_count += 1
        last_line_traced_at = time.time()
        logger.debug("Line Traced")
    logger.debug("Direction: {}".format(pk.dir))


def _move_mouse():
    global mouse_x, mouse_y, mouse_rot, v, line_passed_count

    if not stopped:
        # 1回目に1つ目のコーナーを曲がる前まではシグモイド関数に沿って移動
        if (line_passed_count in [0, 1, 2]) and y <= 3540 and x <= 1485:
            mouse_x = 1100.0  # -285 / (1 + math.e ** (0.0036 * (mouse_y - 2520))) + 1180
            mouse_y = 3540.0

        # 第1、第2カーブは半円に沿って移動 TODO
        elif (line_passed_count in [2, 6, 10]) and 3540 <= y and x <= 1485:
            mouse_x = 1485.0 + CORN_WIDTH / 2
            mouse_y = 5040 - 850.0

        elif (line_passed_count in [2, 6, 10]) and 3540 <= y and 1485 <= x:
            mouse_x = 1485.0 + CORN_WIDTH / 2 + 500
            mouse_y = 3450.0

        # 第2カーブを曲がったらスタートラインに行くまでは直線移動
        elif (line_passed_count in [2, 3, 6, 7, 10, 11]) and 840 <= y <= 3540:
            mouse_x = 2180.0
            mouse_y = 740.0

        # 第3, 4カーブも半円に沿って移動 TODO
        elif (line_passed_count in [3, 4, 7, 8, 11, 12]) and y <= 840 and 1485.0 + CORN_WIDTH / 2 + 400 <= x:
            mouse_x = 1485.0 + CORN_WIDTH / 2 - 200
            mouse_y = 500.0

        # 第4カーブを曲がったら直線移動
        elif (line_passed_count in [3, 4, 7, 8, 11, 12]) and y <= 840 and x <= 1485.0 + CORN_WIDTH / 2:
            mouse_x = 1100.0
            mouse_y = 840.0

        mouse_rot = math.atan2(mouse_y, mouse_x)


# 仮想ネズミを追従する
def _follow_mouse():
    global v_r, v_l, a_v_r, a_v_l, x, y, v, w, p, rot

    delta_theta = math.atan2(mouse_y - y, mouse_x - x) - rot
    distance = math.hypot(mouse_x - x, mouse_y - y)
    # rotation_radius = distance / (2 * math.sin(delta_theta))
    w = 2 * MAX_ANGULAR_VELOCITY * math.sin(delta_theta) / distance
    rot += w * INTERVAL
    v_r = (TIRE_DISTANCE / 2) * w + mouse_v
    v_l = mouse_v - (TIRE_DISTANCE / 2) * w
    v = (v_r + v_l) / 2
    a_v_r = math.degrees(v_r / TIRE_RADIUS)
    a_v_l = math.degrees(v_l / TIRE_RADIUS)
    x += v * math.cos(rot) * INTERVAL
    y += v * math.sin(rot) * INTERVAL
    # logger.debug("mouse: ({}, {})".format(mouse_x, mouse_y))
    # logger.debug("robot: ({}, {})".format(x, y))
    logger.debug(str(a_v_l) + ", " + str(a_v_r))

    pk = BothSteppingMotorPacket(unique_id())
    pk.direction = BothSteppingMotorPacket.ROTATION_FORWARD
    pk.type = BothSteppingMotorPacket.DATA_TYPE_2
    pk.value_1 = a_v_r / 1000
    pk.value_3 = a_v_l / 1000
    connection_manager.data_packet(pk)


# INTERVAL秒起きに実行される
def _heart_beat():
    while core.running:
        # measure(method=measure_line_tracer, callback=on_line_traced)  # ライントレーサの計測
        """SensorManager() \
            .set_packet(MeasureLineTracerPacket(unique_id())) \
            .send() \
            .set_on_receive(lambda pk: on_line_traced(pk))"""

        _move_mouse()  # 仮想ネズミを動かす
        _follow_mouse()  # 仮想ネズミを追従する

        time.sleep(INTERVAL)  # INTERVAL秒待つ
