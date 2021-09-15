import serial
import threading
import core
from queue import Queue
from connection.rpi_to_arduino_packets import RaspberryPiPacket
from connection.arduino_to_rpi_packets import *
from connection.packet_event_listener import PacketEventListener

MOTOR_LEFT = 0   # 左モータ
MOTOR_RIGHT = 1  # 右モータaa

initialized = False  # Arduinoのシリアルポートが初期化されたかどうか

ser: serial.Serial
event_listener = PacketEventListener()
sending_stopped = False  # Arduinoへのパケット送信が可能かどうか
packet_queue = {}  # パケットのキュー


def init():
    print("Initializing serial connection...")

    # ls /devでシリアル通信先を確認!!
    global ser
    ser = serial.Serial('/dev/ttyUSB0', 9600)
    if ser is None:
        print('Error: /dev/ttyUSB0 is not found.')

    print("Starting serial receiver...")
    th = threading.Thread(target=await_packets)
    th.start()

    print("Starting serial sender...")
    th1 = threading.Thread(target=send_packets)
    th1.start()


def data_packet(packet: RaspberryPiPacket):
    packet.encode()

    raw = bytearray(packet.data)
    if core.debug:
        print("\033[32m[SEND]\033[0m (" + str(len(raw)) + ") " + str(raw))

    ser.write(raw)
    ser.flush()


def send_packets():
    while core.running:
        if not sending_stopped:
            pass  # TODO


def await_packets():
    global initialized
    while True:
        if ser.in_waiting <= 0:
            continue

        raw = ser.read_all()
        if core.debug:
            print("\033[34m[RECEIVE]\033[0m (" + str(len(raw)) + ") " + str(raw))

        if (not initialized) and "Transmission Start" in str(raw):
            initialized = True
            event_listener.on_connection_start()
            continue

        try:
            packet = ArduinoPacket(raw)
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



