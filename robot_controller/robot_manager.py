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

MAX_SPEED = (motor_driver.FREQUENCY * motor_driver.STEP_AMOUNT / 360) * (2 * math.pi * TIRE_RADIUS)
R_VR = MAX_SPEED * 0.5
L_VR = MAX_SPEED * 1.0
ROTATION_W = (L_VR - R_VR) / TIRE_DISTANCE

# 自己位置推定（ステージの左上が基準点）
x = 1100.0  # 自己位置x[mm]
y = 840.0 - 180.0  # 自己位置y[mm] 180: ロボット先端から車軸までの長さ
a_v_l = MAX_ANGULAR_VELOCITY  # 左車輪角速度[deg/s]
a_v_r = MAX_ANGULAR_VELOCITY  # 右車輪角速度[deg/s]
v_l = 0.0  # 左車輪の設置点での速度[mm/s]
v_r = 0.0  # 右車輪の設置点での速度[mm/s]
v = 0.0  # 車速[mm/s]
w = 0.0  # 旋回角速度（両車輪の中点）[deg/s]
p = 0.0  # 旋回半径[mm]
rot = 90.0  # ロボットのx軸に対する角度[deg]

distance_1 = 10000.0
previous_distance_1 = 100000.0
distance_2 = 0.0
distance_2_av = 0.0
distance_2_buffer = [0.0, 0.0, 0.0]
fix_dist = 0  # 0 = none, 1 = right, 2 = left
started_at = 0

# 仮想ネズミの座標
mouse_x = 1100.0
mouse_y = 1050.0 - 180.0
mouse_v = 2 * math.pi * TIRE_RADIUS * MAX_ANGULAR_VELOCITY / 360  # (=240.21mm/s)
mouse_rot = 0.0  # 仮想ネズミのx軸に対する角度 [deg]
delta = 150  # 仮想ネズミとロボットの間隔 [mm]
stopped = False  # 仮想ネズミが停止中かどうか

# 状態
state = STATE_READY  # 現在の処理段階
mode = MODE_STRAIGHT
t = 0
first = True
following = True
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

    global started_at
    started_at = time.time()

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
        # line_passed_count += 1


# ライントレースが完了したときのコールバック関数
def on_line_traced(pk: LineTracerResultPacket):
    global last_line_traced_at
    if time.time() - last_line_traced_at > 2.0 and pk.is_on_line:
        last_line_traced_at = time.time()
        update_state()


def on_sensor_data_resulted(pk: SensorDataPacket):
    global line_passed_count, last_line_traced_at, distance_1, distance_2, distance_2_buffer, distance_2_av, following, previous_distance_1
    distance_1 = pk.distance_1
    """distance_2 = pk.distance_2
    distance_2_av = (distance_2_buffer[0] + distance_2_buffer[1] + distance_2_buffer[2]) / 3.0
    distance_2_buffer.pop()
    distance_2_buffer.insert(0, distance_2)"""

    logger.debug("Distance1: {}".format(pk.distance_1))
    # logger.debug("Distance2: {}".format(pk.distance_2))

    if distance_1 < 850 and abs(previous_distance_1 - distance_1) < 800:
        following = False

    previous_distance_1 = distance_1

    if pk.line_tracer == 1 and time.time() - last_line_traced_at > 1.0:
        line_passed_count += 1
        last_line_traced_at = time.time()

        update_state()
        # logger.debug("Line Traced")

        global x, y
        if line_passed_count in [1, 4, 5, 8, 9, 12]:
            # y = 840
            pass
        elif line_passed_count in [2, 3, 6, 7, 10, 11]:
            # y = 2520
            pass

    # logger.debug("Direction: {}".format(pk.dir))


def on_distance_sensor_resulted(pk: DistanceSensorResultPacket):
    def break_following():
        global following
        following = True

    if pk.distance_1 == -1 or pk.distance_2 == -1:
        break_following()
        return

    d_distance = pk.distance_2 - pk.distance_1 if pk.distance_2 > pk.distance_2 else pk.distance_1 - pk.distance_2
    if d_distance < 100 or 10000 < d_distance:
        break_following()
        return

    d_theta = math.atan2(d_distance, 72)

    if pk.distance_2 > pk.distance_1:
        pass


def check_rotation():
    SensorManager() \
        .set_packet(MeasureDistancePacket(unique_id())) \
        .send() \
        .set_on_receive(lambda pk: on_distance_sensor_resulted(pk))


def _move_mouse():
    global mouse_x, mouse_y, mouse_rot, v, line_passed_count, mode, first

    if not stopped:
        if y <= 3540 and x <= 1485 and first:
            mode = MODE_STRAIGHT
            logger.debug("A")
            mouse_x = 1100.0
            mouse_y = 3540.0

        elif y <= 3540 and x <= 1485 and not first:
            mode = MODE_STRAIGHT
            logger.debug("G")
            mouse_x = 1100.0  # -285 / (1 + math.e ** (0.0036 * (mouse_y - 2520))) + 1180
            mouse_y = 3540.0

        # 第1、第2カーブは半円に沿って移動
        elif 3540 <= y and x <= 1485:
            mode = MODE_PURE_PURSUIT
            first = False
            logger.debug("B")
            mouse_x = 1485.0 + CORN_WIDTH / 2
            mouse_y = 5040 - 850.0

        elif 3540 <= y and 1485 <= x:
            mode = MODE_PURE_PURSUIT
            logger.debug("C")
            mouse_x = 1485.0 + CORN_WIDTH / 2 + 500
            mouse_y = 3450.0

        # 第2カーブを曲がったらスタートラインに行くまでは直線移動
        elif 840 <= y <= 3540:
            motor_driver.running_r = False
            motor_driver.running_l = False
            check_rotation()

            mode = MODE_STRAIGHT
            logger.debug("D")
            mouse_x = 2180.0
            mouse_y = 740.0

        # 第3, 4カーブも半円に沿って移動 TODO
        elif y <= 840 and 1485.0 + CORN_WIDTH / 2 + 400 <= x:
            mode = MODE_PURE_PURSUIT
            logger.debug("E")
            mouse_x = 1485.0 + CORN_WIDTH / 2 - 200
            mouse_y = 500.0

        # 第4カーブを曲がったら直線移動
        elif y <= 840 and x <= 1485.0 + CORN_WIDTH / 2:
            mode = MODE_PURE_PURSUIT
            logger.debug("F")
            mouse_x = 1100.0
            mouse_y = 3540.0

        mouse_rot = math.atan2(mouse_y, mouse_x)


# 仮想ネズミを追従する
def _follow_mouse():
    global v_r, v_l, a_v_r, a_v_l, x, y, v, w, p, rot, mode

    # Pure Pursuitアルゴリズムに従う場合
    if mode == MODE_PURE_PURSUIT:
        delta_theta = math.atan2(mouse_y - y, mouse_x - x) - rot
        dist = math.hypot(mouse_x - x, mouse_y - y)
        # rotation_radius = distance / (2 * math.sin(delta_theta))
        w = 4 * MAX_ANGULAR_VELOCITY * math.sin(delta_theta) / dist
        rot += w * INTERVAL
        v_r = (TIRE_DISTANCE / 2) * w + mouse_v
        v_l = mouse_v - (TIRE_DISTANCE / 2) * w
        v = (v_r + v_l) / 2

    # 直進する場合
    elif mode == MODE_STRAIGHT:
        w = 0
        v_r = mouse_v
        v_l = mouse_v
        v = mouse_v

    a_v_r = math.degrees(v_r / TIRE_RADIUS)
    a_v_l = math.degrees(v_l / TIRE_RADIUS)
    x += v * math.cos(rot) * INTERVAL
    y += v * math.sin(rot) * INTERVAL

    logger.debug("({}, {})".format(int(x), int(y)))

    pk = BothSteppingMotorPacket(unique_id())
    pk.direction = BothSteppingMotorPacket.ROTATION_FORWARD
    pk.type = BothSteppingMotorPacket.DATA_TYPE_2
    pk.value_1 = a_v_r / 1000
    pk.value_3 = a_v_l / 1000
    connection_manager.data_packet(pk)


def _heart_beat():
    global t, following, fix_dist
    while core.running:
        if following or time.time() - started_at < 5:
            # _move_mouse()  # 仮想ネズミを動かす
            # _follow_mouse()  # 仮想ネズミを追従する
            motor_driver.move_forward()
            time.sleep(0.2)

        else:
            tt = 0
            while tt <= (math.pi / 2) / ROTATION_W - 0.75:
                motor_driver.move_right()
                time.sleep(0.2)
                tt += 0.2
            following = True

            """if distance_2 < 100:
                tt = 0
                while tt <= 0.1:
                    motor_driver.move_right()
                    time.sleep(0.1)
                    tt += 0.1
                following = True

            else:
                tt = 0
                while tt <= (math.pi / 2) / ROTATION_W - 0.75:
                    motor_driver.move_right()
                    time.sleep(0.2)
                    tt += 0.2
                following = True"""

        t += 1
        check_rotation()
