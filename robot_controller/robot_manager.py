import math
import threading
import time
import logger

import core
from connection.input_packets import *
from connection.output_packets import *
from connection import connection_manager
from sensor.sensor_mamager import SensorManager

# ステート
STATE_READY = 0
STATE_STARTED = 1
STATE_EXCEEDED_SB_LINE = 2
STATE_EXCEEDED_HALF_LINE = 3

# 定数
TIRE_RADIUS = 45.0  # タイヤ半径[mm]
TIRE_DISTANCE = 175.0  # タイヤ同士の距離[mm]
ROTATION_DEGREE = 90.0  # 回転時にタイヤが回る角度[deg]
MAX_ANGULAR_VELOCITY = 1.20 * 1000  # タイヤの最大角速度[deg/s] 14400
INTERVAL = 0.05  # 計測間隔[s]
CORN_WIDTH = 380  # カラーコーンの一辺の長さ[mm]

# 自己位置推定（ステージの左上が基準点）
x = 420.0 + TIRE_DISTANCE / 2  # 自己位置x[mm]
y = 840.0  # 自己位置y[mm]
a_v_l = MAX_ANGULAR_VELOCITY  # 左車輪角速度[deg/s]
a_v_r = MAX_ANGULAR_VELOCITY  # 右車輪角速度[deg/s]
v_l = 0.0  # 左車輪の設置点での速度[mm/s]
v_r = 0.0  # 右車輪の設置点での速度[mm/s]
v = 0.0  # 車速[mm/s]
w = 0.0  # 旋回角速度（両車輪の中点）[deg/s]
p = 0.0  # 旋回半径[mm]
rot = 0.0  # 現在の角度[deg]

# 仮想ネズミの座標
mouse_x = 420.0 + TIRE_DISTANCE / 2
mouse_y = 940.0
stopped = False  # 仮想ネズミが停止中かどうか

# 状態
state = STATE_READY  # 現在の処理段階
direction = 0.0  # degree
line_passed_count = 0
should_update_line = True  # ラインをまたいだことを更新すべきかどうか
last_line_traced_at = 0
measuring_distance = False  # 距離を計測中かどうか
measuring_line_tracer = False  # ライントレーサを計測中かどうか
measuring_nine_axis = False  # 9軸センサで計測中かどうか

_unique_id = 0  # パケットID


def start():
    threading.Thread(target=_heart_beat).start()


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


def _move_mouse():
    global mouse_x, mouse_y, v
    # sigmoid_coefficient = 1485 - (420 + TIRE_DISTANCE / 2 + 400 + CORN_WIDTH / 2)
    if not stopped:
        # 1回目に1つ目のコーナーを曲がる前まではシグモイド関数に沿って移動
        if (line_passed_count in [0, 1, 2]) and y <= 3740:
            mouse_y = y + 100
            mouse_x = -285 / (1 + math.e ** (0.0036 * (mouse_y - 2520))) + 1180

        # 第1、第2カーブは半円に沿って移動 TODO
        elif (line_passed_count in [2, 6, 10]) and 3740 <= y:
            mouse_x = x + 100
            mouse_y = 3550 - math.sqrt(250000 - (mouse_x - 1680) ** 2)

            # 1つめのコーナーを曲がっていたら
            if mouse_x <= 1680:
                mouse_y += 500

        # 第2カーブを曲がったらスタートラインに行くまでは直線移動
        elif (line_passed_count in [2, 3, 6, 7, 10, 11]) and y <= 3740:
            mouse_x = x
            mouse_y = y + 100

        # 第3, 4カーブも半円に沿って移動 TODO
        elif (line_passed_count in [3, 4, 7, 8, 11, 12]) and y <= 900:
            mouse_x = x - 100
            mouse_y = 900 - math.sqrt(250000 - (mouse_x - 1680) ** 2)

            # 1つめのコーナーを曲がっていたら
            if mouse_x <= 1680:
                mouse_y += 500

        # 第4カーブを曲がったら直線移動
        elif (line_passed_count in [5, 6, 9, 10]) and y >= 840:
            mouse_x = x
            mouse_y = y + 100


# 仮想ネズミを追従する
def _follow_mouse():
    k_v = 1.0  # 係数1
    k_t = 0.1  # 係数2
    k_td = 0.1  # 係数3
    global v_r, v_l, a_v_r, a_v_l, x, y, v, w, p, rot

    delta_theta = math.atan2(mouse_y - y, mouse_x - x) - rot
    delta_v = k_t * delta_theta + k_td * (delta_theta / INTERVAL)
    v = k_v * math.sqrt((mouse_x - x) ** 2 + (mouse_y - y) ** 2)
    a_v_r = (v + delta_v) / TIRE_RADIUS
    a_v_l = (v - delta_v) / TIRE_RADIUS
    logger.debug(str(a_v_r) + ", " + str(a_v_l))

    pk = BothSteppingMotorPacket(unique_id())
    pk.direction = BothSteppingMotorPacket.ROTATION_FORWARD
    pk.type = BothSteppingMotorPacket.DATA_TYPE_2
    pk.value_1 = MAX_ANGULAR_VELOCITY / 1000
    pk.value_2 = INTERVAL * 6000
    pk.value_3 = MAX_ANGULAR_VELOCITY / 1000
    pk.value_4 = INTERVAL * 6000
    connection_manager.data_packet(pk)

    """
    r_pk = RightSteppingMotorPacket(unique_id())
    r_pk.direction = RightSteppingMotorPacket.ROTATION_RIGHT
    r_pk.type = RightSteppingMotorPacket.DATA_TYPE_1
    r_pk.value_1 = a_v_r / 1000
    r_pk.value_2 = INTERVAL * 1000
    connection_manager.data_packet(r_pk)

    l_pk = LeftSteppingMotorPacket(unique_id())
    l_pk.direction = LeftSteppingMotorPacket.ROTATION_LEFT
    l_pk.type = LeftSteppingMotorPacket.DATA_TYPE_1
    l_pk.value_1 = a_v_l / 1000
    l_pk.value_2 = INTERVAL * 1000
    connection_manager.data_packet(l_pk)
    """


# INTERVAL秒起きに実行される
def _heart_beat():
    while core.running:
        # 各値の更新
        global v_r, v_l, a_v_r, a_v_l, x, y, v, w, p, rot
        v_r = TIRE_RADIUS * math.radians(a_v_r)
        v_l = TIRE_RADIUS * math.radians(a_v_l)
        p = TIRE_DISTANCE * (v_r + v_l) / (v_r - v_l) if v_r - v_l != 0 else -1
        w = (v_r - v_l) / TIRE_DISTANCE
        v = (v_r + v_l) / 2
        rot = w * INTERVAL
        x += v * math.cos(rot)
        y += v * math.sin(rot)

        # measure(method=measure_line_tracer, callback=on_line_traced)  # ライントレーサの計測
        SensorManager() \
            .set_packet(MeasureLineTracerPacket(unique_id())) \
            .send() \
            .set_on_receive(lambda pk: on_line_traced(pk))

        _move_mouse()  # 仮想ネズミを動かす
        _follow_mouse()  # 仮想ネズミを追従する

        time.sleep(INTERVAL)  # INTERVAL秒待つ
