import robot_manager
import threading
import time
import controller_board_manager
import logger
from sensor.sensor_mamager import SensorManager
from connection.input_packets import *
from connection.output_packets import *


debug = True  # デバッグモード
running = False  # 実行中かどうか


class Core:

    lost_ball = False  # ボールを保持しているかどうか
    last_line_traced_at = 0  # 最後にライン上であることを検出した時間（エポック秒）

    # 外部インタフェースとの接続が完了したとき
    def on_connection_start(self, interface_name):
        logger.info("Successfully connected.")
        SensorManager() \
            .set_packet(MeasureNineAxisSensorPacket(robot_manager.unique_id())) \
            .send() \
            .set_on_receive(lambda pk: self.on_nine_axis_sensor_resulted(pk))

    # 9軸センサの計測が完了したときに発火
    def on_nine_axis_sensor_resulted(self, pk: NineAxisSensorResultPacket):
        if debug:
            logger.debug("GeoMagnetism: " + str(pk.geomagnetism))

        robot_manager.start()

    # 状態監視
    def manage_state(self):
        thread = threading.Thread(target=self._do_managing_state)
        thread.start()

    # stateを取得し、標準出力に出力する
    def _do_managing_state(self):
        while running:
            logger.state(str(self.state))
            time.sleep(1)
        logger.critical("Stopped program by the controller.")
        exit(0)


instance: Core
# instance = Core()

if __name__ == "__main__":
    # LEDインジケータ
    controller_board_manager.init()  # 開始ボタンが押されるまでここでブロッキングされる
    controller_board_manager.yellow_led_on()
    controller_board_manager.red_led_off()

    # シリアル通信モジュールの初期化
    robot_manager.connection_manager.init()

    if debug:
        # instance.manage_state()
        pass

