import robot_manager
import threading
import time
from sensor.sensor_mamager import SensorManager
from connection.arduino_to_rpi_packets import *
from connection.rpi_to_arduino_packets import *


debug = True  # デバッグモード
running = True  # 実行中かどうか


class Core:
    STATE_READY = -1  # 電源投入後
    STATE_STAND_BY = 0  # センサ計測完了
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

    lost_ball = False  # ボールを保持しているかどうか
    state = STATE_READY  # 処理段階
    last_line_traced_at = 0

    # Arduinoとの接続が完了したとき
    def on_connection_start(self):
        print("Process Started.")
        SensorManager() \
            .set_packet(MeasureNineAxisSensorPacket(robot_manager.rand())) \
            .send() \
            .set_on_receive(lambda pk: self.on_nine_axis_sensor_resulted(pk))

    # 9軸センサの計測が完了したとき
    def on_nine_axis_sensor_resulted(self, pk: NineAxisSensorResultPacket):
        if debug:
            print("\033[35m[DEBUG] GeoMagnetism: \033[0m" + str(pk.geomagnetism))

        if self.state == self.STATE_READY:
            self.state = self.STATE_STAND_BY
            robot_manager.direction = pk.geomagnetism  # TODO pkから方角を読み取って記録する
            robot_manager.go_straight()
            robot_manager.measure(robot_manager.measure_line_tracer, self.on_line_tracer_resulted)
            return

        elif self.state == self.STATE_PHASE_1_EXCEEDED_HALF_LINE_1:
            if abs(90 - abs(robot_manager.direction - pk.geomagnetism)) < 2:
                self.state = self.STATE_PHASE_1_TURNED_CORNER_1
                robot_manager.stop_measuring_nine_axis()
                robot_manager.stop()
                robot_manager.go_straight()
                robot_manager.measure(robot_manager.measure_distance, self.on_distance_sensor_resulted)

        elif self.state == self.STATE_PHASE_1_TURNED_CORNER_1:
            if abs(180 - abs(robot_manager.direction - pk.geomagnetism)) < 2:
                self.state = self.STATE_PHASE_1_TURNED_CORNER_2
                robot_manager.stop_measuring_nine_axis()
                robot_manager.stop()
                robot_manager.go_straight()
                robot_manager.measure(robot_manager.measure_line_tracer, self.on_line_tracer_resulted)

        elif self.state == self.STATE_PHASE_1_EXCEEDED_SB_LINE:
            if abs(270 - abs(robot_manager.direction - pk.geomagnetism)) < 2:
                self.state = self.STATE_PHASE_1_TURNED_CORNER_3
                robot_manager.stop_measuring_nine_axis()
                robot_manager.stop()
                robot_manager.go_straight()
                robot_manager.measure(robot_manager.measure_distance, self.on_distance_sensor_resulted)

        elif self.state == self.STATE_PHASE_1_TURNED_CORNER_3:
            print(robot_manager.direction - pk.geomagnetism)
            if abs(360 - abs(robot_manager.direction - pk.geomagnetism)) < 2:
                self.state = self.STATE_PHASE_1_TURNED_CORNER_4
                robot_manager.stop_measuring_nine_axis()
                robot_manager.stop()
                robot_manager.go_straight()
                robot_manager.measure(robot_manager.measure_line_tracer, self.on_line_tracer_resulted)

    # ライントレーサの計測が完了したとき
    def on_line_tracer_resulted(self, pk: LineTracerResultPacket):
        if debug:
            print("\033[35m[DEBUG] LineTracer: \033[0m" + str(pk.is_on_line))

        # ライン上にあることが連続で検知されないよう2秒以内に連続で来た場合にははじく
        if not pk.is_on_line or (int(time.time()) - self.last_line_traced_at < 2):
            return

        self.last_line_traced_at = int(time.time())
        robot_manager.stop_measuring_line_tracer()

        if self.state == self.STATE_STAND_BY\
                or self.state == self.STATE_PHASE_1_TURNED_CORNER_4:

            if self.state == self.STATE_STAND_BY:
                self.state = self.STATE_PHASE_1_STARTED
            elif self.STATE_PHASE_1_TURNED_CORNER_4:
                self.state = self.STATE_PHASE_2_STARTED

            robot_manager.measure(robot_manager.measure_line_tracer, self.on_line_tracer_resulted)

        elif self.state == self.STATE_PHASE_1_STARTED:
            self.state = self.STATE_PHASE_1_EXCEEDED_HALF_LINE_1
            robot_manager.measure(robot_manager.measure_distance, self.on_distance_sensor_resulted)

        elif self.state == self.STATE_PHASE_1_TURNED_CORNER_2:
            self.state = self.STATE_PHASE_1_EXCEEDED_HALF_LINE_2
            robot_manager.measure(robot_manager.measure_line_tracer, self.on_line_tracer_resulted)

        elif self.state == self.STATE_PHASE_1_EXCEEDED_HALF_LINE_2:
            self.state = self.STATE_PHASE_1_EXCEEDED_SB_LINE
            robot_manager.measure(robot_manager.measure_distance, self.on_distance_sensor_resulted)

    # 距離センサの計測が完了したとき
    def on_distance_sensor_resulted(self, pk: DistanceSensorResultPacket):
        if debug:
            print("\033[35m[DEBUG] Distance: \033[0m" + str(pk.distance))
        if self.state == self.STATE_PHASE_1_EXCEEDED_HALF_LINE_1:
            if pk.distance < 1000:
                robot_manager.stop_measuring_distance()
                robot_manager.stop()
                robot_manager.rotate_right()
                robot_manager.measure(robot_manager.measure_nine_axis, self.on_nine_axis_sensor_resulted)

        elif self.state == self.STATE_PHASE_1_TURNED_CORNER_1:
            if pk.distance < 1335:
                robot_manager.stop_measuring_distance()
                robot_manager.stop()
                robot_manager.rotate_right()
                robot_manager.measure(robot_manager.measure_nine_axis, self.on_nine_axis_sensor_resulted)

        elif self.state == self.STATE_PHASE_1_EXCEEDED_SB_LINE:
            if pk.distance < 700:
                robot_manager.stop_measuring_distance()
                robot_manager.stop()
                robot_manager.rotate_right()
                robot_manager.measure(robot_manager.measure_nine_axis, self.on_nine_axis_sensor_resulted)

        elif self.state == self.STATE_PHASE_1_TURNED_CORNER_3:
            if pk.distance < 1335:
                robot_manager.stop_measuring_distance()
                robot_manager.stop()
                robot_manager.rotate_right()
                robot_manager.measure(robot_manager.measure_nine_axis, self.on_nine_axis_sensor_resulted)

    # 状態監視
    def manage_state(self):
        thread = threading.Thread(target=self._do_managing_state)
        thread.start()

    def _do_managing_state(self):
        while running:
            print("\033[33m[STATE] \033[0m" + str(self.state))
            time.sleep(1)


instance = Core()

if __name__ == "__main__":

    # シリアル通信モジュールの初期化
    robot_manager.connection_manager.init()

    if debug:
        # instance.manage_state()
        pass

