import serial
import threading
import core
import time
from connection.rpi_to_arduino_packets import RaspberryPiPacket
from connection.arduino_to_rpi_packets import *
from connection.packet_event_listener import PacketEventListener

MOTOR_LEFT = 0  # 左モータ
MOTOR_RIGHT = 1  # 右モータaa

initialized = False  # Arduinoのシリアルポートが初期化されたかどうか

ser: serial.Serial
event_listener = PacketEventListener()
sending_stopped = False  # Arduinoへのパケット送信が可能かどうか
packet_key_queue = []  # パケット（rand_id）のキュー
packet_queue = {}  # パケットのキュー


def init():
    print("Initializing serial connection...")

    # ls /devでシリアル通信先を確認!!
    global ser
    ser = serial.Serial('/dev/ttyUSB0', 9600)
    if ser is None:
        print('Error: /dev/ttyUSB0 is not found.')

    print("Starting serial receiver...")
    th = threading.Thread(target=_await_packets)
    th.start()

    print("Starting serial sender...")
    th1 = threading.Thread(target=_send_packets)
    th1.start()


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

    ser.write(raw)
    ser.flush()


# パケット受信待機
def _await_packets():
    global initialized
    while core.running:
        if ser.in_waiting <= 0:
            continue

        raw = ser.read_all()
        raw_str = str(raw)

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
            elif text.isdecimal():
                sending_stopped = False  # パケット送信停止解除
                del packet_queue[int(text)]
                continue

            # Arduino to Raspberry Pi Packet
            # TODO RaspberryPiPacket to ArduinoPacket
            elif len(text) >= ArduinoPacket.PACKET_LENGTH and len(text) % 4 == 0:
                split_text = text.split("\\")
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

            # 予期しないパケットのとき
            else:
                print("\033[31m[ERROR] \033[0mInvalid Packet Error (" + text + ")")
                continue

        # 受信パケットの処理
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

            elif packet.packet_id == ServoMotorFeedbackPacket.ID:
                pk = ServoMotorFeedbackPacket(packet.data)
                pk.decode()
                event_listener.on_servo_motor_feedback(pk)

        except AssertionError:
            continue
