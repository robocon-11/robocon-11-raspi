import serial
import threading
import core
import time
from connection.interface.connection_interface import ConnectionInterface
from connection.interface.serial_interface import SerialInterface
from connection.interface.network_interface import NetworkInterface
from connection.rpi_to_arduino_packets import RaspberryPiPacket
from connection.arduino_to_rpi_packets import *
from connection.packet_event_listener import PacketEventListener

MOTOR_LEFT = 0  # 左モータ
MOTOR_RIGHT = 1  # 右モータaa

connection_interface = SerialInterface()  # 通信インターフェース（シリアルorネットワーク）
event_listener = PacketEventListener()
initialized = False  # Arduinoのシリアルポートが初期化されたかどうか
sending_stopped = False  # Arduinoへのパケット送信が可能かどうか
packet_key_queue = []  # パケット（rand_id）のキュー
packet_queue = {}  # パケットのキュー


def init():
    print("Initializing connection interface...")
    connection_interface.init()

    print("Starting packet receiver...")
    th = threading.Thread(target=_await_packets)
    th.start()

    print("Starting packet sender...")
    th1 = threading.Thread(target=_send_packets)
    th1.start()


def add_sensor_manager(rand_id, sensor_manager):
    event_listener.add_manager(rand_id, sensor_manager)


# キューにパケットを追加する
def data_packet(packet: RaspberryPiPacket):
    packet.encode()
    packet_key_queue.append(packet.rand_id)
    packet_queue[packet.rand_id] = packet


# パケット送信のキューイング
def _send_packets():
    while core.running:
        if not sending_stopped and not len(packet_key_queue) == 0:
            rand_id = packet_key_queue.pop()
            pk = packet_queue[rand_id]
            _send_packet(pk)

        time.sleep(0.01)  # 10ms待つ


# パケットを送信する
def _send_packet(pk):
    raw = bytearray(pk.data)

    if core.debug:
        print("\033[32m[SEND]\033[0m (" + str(len(raw)) + ") " + str(raw))
        print("\033[33m[STATE] \033[0m" + str(core.instance.state))

    connection_interface.send_data(raw)


# パケット受信待機
def _await_packets():
    global initialized
    while core.running:
        if connection_interface.is_waiting():
            continue

        raw = connection_interface.read_data()
        raw_str = str(raw).replace("\\t", "\\x09")

        if core.debug:
            print("\033[34m[RECEIVE]\033[0m (" + str(len(raw)) + ") " + raw_str)

        # 通信開始
        if (not initialized) and "Transmission Start" in raw_str:
            initialized = True
            event_listener.on_connection_start()
            continue

        # データサイズエラー
        if "Invalid data size" in raw_str:
            print("\033[31m[ERROR] \033[0mInvalid Data Size Error")
            continue

        # 受信データを\r\nで区切って処理
        split = raw_str[2:len(raw_str) - 1].split("\\r\\n")
        global sending_stopped

        pk_data = []
        for text in split:
            # パケット送信停止命令
            if text == "Stop":
                sending_stopped = True
                continue

            # 受信信号（rand_id）
            elif text.isdecimal() and len(text) == 4:
                sending_stopped = False  # パケット送信停止解除
                del packet_queue[int(text)]
                continue

            # Arduino to Raspberry Pi Packet
            # TODO RaspberryPiPacket to ArduinoPacket
            elif len(text) >= ArduinoPacket.PACKET_LENGTH:
                split_text = text[1:].split("\\")
                ids = []
                i = 0
                for x in split_text:
                    if i <= ArduinoPacket.PACKET_LENGTH:
                        pk_data.append(x[2:3])
                    else:
                        ids.append(x[2:3])
                    i = i + 1

                # キューからパケットを削除
                if len(ids) == 4:
                    sending_stopped = False  # パケット送信停止解除
                    del packet_queue[int("".join(ids))]

                _process_packet(pk_data)

            # 予期しないパケットのとき
            else:
                # print("\033[31m[ERROR] \033[0mInvalid Packet Error (" + text + ")")
                continue


# 受信パケットの処理
def _process_packet(pk_data):
    try:
        packet = ArduinoPacket(pk_data)
        packet.decode()

        if packet.packet_id == RightSteppingMotorAlertPacket.ID:
            pk = RightSteppingMotorAlertPacket(packet.data)
            pk.decode()
            event_listener.on_right_stepping_motor_alerted(pk)

        elif packet.packet_id == RightSteppingMotorFeedbackPacket.ID:
            pk = RightSteppingMotorFeedbackPacket(packet.data)
            pk.decode()
            event_listener.on_right_stepping_motor_feedback(pk)

        elif packet.packet_id == LeftSteppingMotorAlertPacket.ID:
            pk = LeftSteppingMotorAlertPacket(packet.data)
            pk.decode()
            event_listener.on_left_stepping_motor_alerted(pk)

        elif packet.packet_id == LeftSteppingMotorFeedbackPacket.ID:
            pk = LeftSteppingMotorFeedbackPacket(packet.data)
            pk.decode()
            event_listener.on_left_stepping_motor_feedback(pk)

        elif packet.packet_id == DistanceSensorResultPacket.ID:
            pk = DistanceSensorResultPacket(packet.data)
            pk.decode()
            event_listener.on_distance_sensor_resulted(pk)

        elif packet.packet_id == LineTracerResultPacket.ID:
            pk = LineTracerResultPacket(packet.data)
            pk.decode()
            event_listener.on_line_tracer_resulted(pk)

        elif packet.packet_id == NineAxisSensorResultPacket.ID:
            pk = NineAxisSensorResultPacket(packet.data)
            pk.decode()
            event_listener.on_nine_axis_sensor_resulted(pk)

        elif packet.packet_id == UpperServoMotorFeedbackPacket.ID:
            pk = UpperServoMotorFeedbackPacket(packet.data)
            pk.decode()
            event_listener.on_upper_servo_motor_feedback(pk)

        elif packet.packet_id == BottomServoMotorFeedbackPacket.ID:
            pk = BottomServoMotorFeedbackPacket(packet.data)
            pk.decode()
            event_listener.on_bottom_servo_motor_feedback(pk)

    except AssertionError as e:
        print(e)
        return



