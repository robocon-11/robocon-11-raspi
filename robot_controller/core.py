import robot_manager
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
    initialized = False

    # 外部インタフェースとの接続が完了したとき
    def on_connection_start(self, interface_name):
        logger.info("Successfully connected: {}".format(interface_name))

        if not self.initialized:
            self.initialized = True
            SensorManager() \
                .set_packet(MeasureNineAxisSensorPacket(robot_manager.unique_id())) \
                .send() \
                .set_on_receive(lambda pk: self.on_nine_axis_sensor_resulted(pk))

    # 9軸センサの計測が完了したときに発火
    def on_nine_axis_sensor_resulted(self, pk: NineAxisSensorResultPacket):
        robot_manager.start()


instance: Core

if __name__ == "__main__":
    # LEDインジケータ
    controller_board_manager.init()  # 開始ボタンが押されるまでここでブロッキングされる
    controller_board_manager.yellow_led_on()
    controller_board_manager.red_led_off()

    # シリアル通信モジュールの初期化
    robot_manager.connection_manager.init()
