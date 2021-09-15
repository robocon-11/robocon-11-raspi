import robot_manager
import threading
import time
from connection import connection_manager
from sensor.sensor_mamager import SensorManager
from connection.arduino_to_rpi_packets import *
from connection.rpi_to_arduino_packets import *
#a
STATE_STAND_BY = 0  # 電源投入後
STATE_PHASE_1_STARTED = 1  # 1回目に左側のS/Bラインを超えた
STATE_PHASE_1_EXCEEDED_HALF_LINE_1 = 17  # 1回目に中心線を超えた
STATE_PHASE_1_TURNED_CORNER_1 = 2  # スタート後1つめの角を曲がった
STATE_PHASE_1_TURNED_CORNER_2 = 3  # スタート後2つめの角を曲がった
STATE_PHASE_1_EXCEEDED_HALF_LINE_2 = 18  # 2回目に中心線を超えた
STATE_PHASE_1_EXCEEDED_SB_LINE = 19  # S/Bラインを超えた
STATE_PHASE_1_TURNED_CORNER_3 = 4  # スタート後3つめの角を曲がった
STATE_PHASE_1_TURNED_CORNER_4 = 5  # スタート後4つめの角を曲がった
STATE_PHASE_2_STARTED = 6  # 2回目に左側のS/Bラインを超えた
STATE_PHASE_2_EXCEEDED_HALF_LINE_1 = 20
STATE_PHASE_2_TURNED_CORNER_1 = 7
STATE_PHASE_2_TURNED_CORNER_2 = 8
STATE_PHASE_2_EXCEEDED_HALF_LINE_2 = 21
STATE_PHASE_2_EXCEEDED_SB_LINE = 22
STATE_PHASE_2_TURNED_CORNER_3 = 9
STATE_PHASE_2_TURNED_CORNER_4 = 10
STATE_PHASE_3_STARTED = 11  # 3回目に左側のS/Bラインを超えた
STATE_PHASE_3_EXCEEDED_HALF_LINE_1 = 23
STATE_PHASE_3_TURNED_CORNER_1 = 12
STATE_PHASE_3_TURNED_CORNER_2 = 13
STATE_PHASE_3_EXCEEDED_HALF_LINE_2 = 24
STATE_PHASE_3_EXCEEDED_SB_LINE = 25
STATE_PHASE_3_TURNED_CORNER_3 = 14
STATE_PHASE_3_TURNED_CORNER_4 = 15
STATE_FINISHED = 16  # 4回目に左側のS/Bラインを超えた

debug = True  # デバッグモード

running = True  # 実行中かどうか
lost_ball = False  # ボールを保持しているかどうか
state = STATE_STAND_BY  # 処理段階


def on_connection_start():
    print("Process Started.")
    SensorManager() \
        .set_packet(MeasureNineAxisSensorPacket(robot_manager.rand())) \
        .send() \
        .set_on_receive(lambda pk: on_nine_axis_sensor_resulted(pk))


def on_nine_axis_sensor_resulted(pk: NineAxisSensorResultPacket):
    global state
    if state == STATE_STAND_BY:
        robot_manager.direction = 2  # TODO pkから方角を読み取って記録する
        robot_manager.go_straight()
        robot_manager.measure(robot_manager.measure_line_tracer(method=on_line_tracer_resulted))


def on_line_tracer_resulted(pk: LineTracerResultPacket):
    if not pk.on_line:
        return

    robot_manager.stop_measuring_line_tracer()

    global state
    if state == STATE_STAND_BY:
        state = STATE_PHASE_1_STARTED
        robot_manager.measure(robot_manager.measure_line_tracer(method=on_line_tracer_resulted))

    elif state == STATE_PHASE_1_STARTED:
        state = STATE_PHASE_1_EXCEEDED_HALF_LINE_1
        robot_manager.measure(robot_manager.measure_distance(method=on_distance_sensor_resulted))


def on_distance_sensor_resulted(pk: MeasureDistanceToBallPacket):
    global state
    if state == STATE_PHASE_1_EXCEEDED_HALF_LINE_1:
        if pk.direction < 900:
            robot_manager.stop_measuring_distance()
            # robot_manager.stop()
            robot_manager.rotate_right()

    pass


def manage_state():
    thread = threading.Thread(target=_do_managing_state)
    thread.start()


def _do_managing_state():
    while running:
        print("\033[31m[STATE] \033[0m" + str(state))
        time.sleep(1)


if __name__ == "__main__":
    if debug:
        manage_state()

    connection_manager.init()


# def do_rotation_phase():



