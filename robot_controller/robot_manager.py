import math
import threading
import time

import core
from connection import connection_manager
from connection.output_packets import *
from sensor.sensor_mamager import SensorManager

STATE_READY = 0  # 電源投入後
STATE_STAND_BY = 1  # センサ計測完了
STATE_PHASE_1_STARTED = 2  # 1回目に左側のS/Bラインを超えた
STATE_PHASE_1_EXCEEDED_HALF_LINE_1 = 3  # 1回目に中心線を超えた
STATE_PHASE_1_TURNED_CORNER_1 = 4  # スタート後1つめの角を曲がった
STATE_PHASE_1_TURNED_CORNER_2 = 5  # スタート後2つめの角を曲がった
STATE_PHASE_1_EXCEEDED_HALF_LINE_2 = 6  # 2回目に中心線を超えた
STATE_PHASE_1_EXCEEDED_SB_LINE = 7  # S/Bラインを超えた
STATE_PHASE_1_TURNED_CORNER_3 = 8  # スタート後3つめの角を曲がった
STATE_PHASE_1_TURNED_CORNER_4 = 9  # スタート後4つめの角を曲がった
STATE_PHASE_2_STARTED = 10  # 2回目に左側のS/Bラインを超えた
STATE_PHASE_2_EXCEEDED_HALF_LINE_1 = 11
STATE_PHASE_2_TURNED_CORNER_1 = 12
STATE_PHASE_2_TURNED_CORNER_2 = 13
STATE_PHASE_2_EXCEEDED_HALF_LINE_2 = 14
STATE_PHASE_2_EXCEEDED_SB_LINE = 15
STATE_PHASE_2_TURNED_CORNER_3 = 16
STATE_PHASE_2_TURNED_CORNER_4 = 17
STATE_PHASE_3_STARTED = 18  # 3回目に左側のS/Bラインを超えた
STATE_PHASE_3_EXCEEDED_HALF_LINE_1 = 19
STATE_PHASE_3_TURNED_CORNER_1 = 20
STATE_PHASE_3_TURNED_CORNER_2 = 21
STATE_PHASE_3_EXCEEDED_HALF_LINE_2 = 22
STATE_PHASE_3_EXCEEDED_SB_LINE = 23
# STATE_PHASE_3_TURNED_CORNER_3 = 24
# STATE_PHASE_3_TURNED_CORNER_4 = 25
STATE_FINISHED = 100  # 4回目に左側のS/Bラインを超えた

# 定数
TIRE_RADIUS = 45.0  # タイヤ半径[mm]
TIRE_DISTANCE = 180.0  # TODO タイヤ同士の距離[mm]
ROTATION_DEGREE = 90.0  # 回転時にタイヤが回る角度[deg]
MAX_ANGULAR_VELOCITY = 264.7  # タイヤの最大角速度[deg/s]
INTERVAL = 0.1  # 計測間隔[s]
CORN_WIDTH = 380  # カラーコーンの一辺の長さ[mm]

# 自己位置推定（ステージの左上が基準点）
x = 840.0  # 自己位置x[mm]
y = 0.0  # 自己位置y[mm]
a_v_l = MAX_ANGULAR_VELOCITY  # 左車輪角速度[deg/s]
a_v_r = MAX_ANGULAR_VELOCITY  # 右車輪角速度[deg/s]
v_l = 0.0  # 左車輪の設置点での速度[mm/s]
v_r = 0.0  # 右車輪の設置点での速度[mm/s]
v = 0.0  # 車速[mm/s]
w = 0.0  # 旋回角速度（両車輪の中点）[deg/s]
p = 0.0  # 旋回半径[mm]
rot = 0.0  # 現在の角度[deg]
state = STATE_READY  # 現在の処理段階
stopped = False  # 追尾先が停止中かどうか

mouse_x = 850.0
mouse_y = 420.0 + TIRE_DISTANCE / 2

direction = 0.0  # degree
measuring_distance = False  # 距離を計測中かどうか
measuring_line_tracer = False  # ライントレーサを計測中かどうか
measuring_nine_axis = False  # 9軸センサで計測中かどうか

_unique_id = 0  # パケットID


def start():
    threading.Thread(target=_heart_beat).start()


# 右に90度回転
def rotate_right():
    pk_r = RightSteppingMotorPacket(unique_id())
    pk_r.direction = RightSteppingMotorPacket.ROTATION_LOCKED
    pk_r.type = RightSteppingMotorPacket.DATA_TYPE_3
    connection_manager.data_packet(pk_r)

    pk_l = LeftSteppingMotorPacket(unique_id())
    pk_l.direction = OutputPacket.ROTATION_LEFT
    pk_l.type = RightSteppingMotorPacket.DATA_TYPE_3
    # pk_l.data_1 = create_filled_data1(ROTATION_DEGREE)
    connection_manager.data_packet(pk_l)


# 左に90度回転
def rotate_left():
    pk_l = LeftSteppingMotorPacket(unique_id())
    pk_l.direction = LeftSteppingMotorPacket.ROTATION_LOCKED
    connection_manager.data_packet(pk_l)

    pk_r = RightSteppingMotorPacket(unique_id())
    pk_r.direction = OutputPacket.ROTATION_LEFT
    pk_r.data_1 = create_filled_data1(ROTATION_DEGREE)
    connection_manager.data_packet(pk_l)


# 指定された距離だけ直進
# @arg distance(mm)
def go_straight_distance(distance):
    pk = BothSteppingMotorPacket(unique_id())
    pk.direction = BothSteppingMotorPacket.ROTATION_RIGHT
    pk.type = BothSteppingMotorPacket.DATA_TYPE_1
    # TODO 角速度と総角度 360 * distance / (TIRE_RADIUS * 2 * math.pi)
    connection_manager.data_packet(pk)


# 続けて前進
def go_straight():
    pk = BothSteppingMotorPacket(unique_id())
    pk.direction = BothSteppingMotorPacket.ROTATION_RIGHT
    pk.type = BothSteppingMotorPacket.DATA_TYPE_3
    connection_manager.data_packet(pk)


# 停止
def stop():
    pk = BothSteppingMotorPacket(unique_id())
    pk.direction = BothSteppingMotorPacket.ROTATION_LOCKED
    pk.type = BothSteppingMotorPacket.DATA_TYPE_4
    connection_manager.data_packet(pk)


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


# 1つの単浮動小数点数を8byteの配列に変換する
def create_filled_data1(a: float):
    return create_filled_data2(a, 0.0)


# 2つの単浮動小数点数を8byteの配列に変換する
def create_filled_data2(a: float, b: float):
    return struct.pack("f", a) + struct.pack("f", b)


# 2つの単浮動小数点数からなる8byteのbyte配列を長さ2のfloat配列に変換する
def divide_data(data):
    return [struct.unpack("f", bytes(data[0:4]))[0], struct.unpack("f", bytes(data[4:8]))[0]]


# ランダムなパケットIDを生成
def unique_id():
    global _unique_id
    result = _unique_id
    _unique_id += 1
    return result


def _mouse_running():
    global mouse_x, mouse_y, v
    sigmoid_coefficient = 1485 - (420 + TIRE_DISTANCE / 2 + 400 + CORN_WIDTH / 2)
    if not stopped:
        # 1回目に1つ目のコーナーを曲がる前まではシグモイド関数に沿って移動
        if (state == STATE_STAND_BY
            or state == STATE_PHASE_1_STARTED
            or state == STATE_PHASE_1_EXCEEDED_HALF_LINE_1) and x <= 3740:
            mouse_x = x + 100
            mouse_y = - (sigmoid_coefficient / (1 + math.e ** (0.00336 * (mouse_x - 2520))) - (
                    420 + TIRE_DISTANCE / 2 + 400 + CORN_WIDTH / 2))  # sigmoid function

        # 第1、第2カーブは半円に沿って移動
        elif (state == STATE_PHASE_1_EXCEEDED_HALF_LINE_1
              or state == STATE_PHASE_2_EXCEEDED_HALF_LINE_1
              or state == STATE_PHASE_3_EXCEEDED_HALF_LINE_1
              or state == STATE_PHASE_1_TURNED_CORNER_1
              or state == STATE_PHASE_2_TURNED_CORNER_1
              or state == STATE_PHASE_3_TURNED_CORNER_1) and 3740 <= x:
            mouse_x = x + 100
            mouse_y = 1485 - math.sqrt(348100 - (mouse_x - 3740) ** 2)

            # 1つめのコーナーを曲がっていたら
            if state == STATE_PHASE_1_TURNED_CORNER_1 \
                    or state == STATE_PHASE_2_TURNED_CORNER_1 \
                    or state == STATE_PHASE_3_TURNED_CORNER_1:
                mouse_y += 400 + CORN_WIDTH

        # 第2カーブを曲がったらスタートラインに行くまでは直線移動
        elif (state == STATE_PHASE_1_TURNED_CORNER_2
              or state == STATE_PHASE_2_TURNED_CORNER_2
              or state == STATE_PHASE_3_TURNED_CORNER_2
              or state == STATE_PHASE_1_EXCEEDED_HALF_LINE_2
              or state == STATE_PHASE_2_EXCEEDED_HALF_LINE_2
              or state == STATE_PHASE_3_EXCEEDED_HALF_LINE_2) and x <= 3740:
            mouse_x = x - 100
            mouse_y = 1485 + 400 + TIRE_DISTANCE / 2  # + CORN_WIDTH / 2

        # 第3, 4カーブも半円に沿って移動
        elif (state == STATE_PHASE_1_EXCEEDED_SB_LINE
              or state == STATE_PHASE_2_EXCEEDED_SB_LINE
              or state == STATE_PHASE_3_EXCEEDED_SB_LINE
              or state == STATE_PHASE_1_TURNED_CORNER_3
              or state == STATE_PHASE_2_TURNED_CORNER_3) and x <= 840:
            mouse_x = x - 100
            mouse_y = 1485 - math.sqrt(240100 - (mouse_x - 840) ** 2) + 490

            # 3つめのコーナーを曲がっていたら
            if state == STATE_PHASE_1_TURNED_CORNER_1 \
                    or state == STATE_PHASE_2_TURNED_CORNER_1 \
                    or state == STATE_PHASE_3_TURNED_CORNER_1:
                mouse_y -= 490

        # 第4カーブを曲がったら直線移動
        elif (state == STATE_PHASE_1_TURNED_CORNER_4
              or state == STATE_PHASE_2_TURNED_CORNER_4
              or state == STATE_PHASE_2_EXCEEDED_SB_LINE
              or state == STATE_PHASE_3_EXCEEDED_SB_LINE
              or state == STATE_PHASE_2_EXCEEDED_HALF_LINE_1
              or state == STATE_PHASE_3_EXCEEDED_HALF_LINE_1) and x <= 840:
            mouse_x = x + 100
            mouse_y = - (220 * mouse_x / 2900 - 1053.72)


def _heart_beat():
    while core.running:
        _mouse_running()

        global v_r, v_l, a_v_r, a_v_l, x, y, v, w, p, rot
        v_r = TIRE_RADIUS / (a_v_r / INTERVAL)
        v_l = TIRE_RADIUS / (a_v_l / INTERVAL)
        p = TIRE_DISTANCE * (v_r + v_l) / (v_r - v_l) if v_r - v_l != 0 else -1
        w = (v_r - v_l) / (2 * TIRE_DISTANCE)
        v = (v_r + v_l) / 2
        rot = w * INTERVAL
        x += v * math.cos(rot)
        y += v * math.sin(rot)
