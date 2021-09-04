import serial
import threading
from connection.rpi_to_arduino_packets import RaspberryPiPacket
from connection.arduino_to_rpi_packets import *
from connection.packet_event_listener import PacketEventListener

MOTOR_LEFT = 0   # 左モータ
MOTOR_RIGHT = 1  # 右モータ

ser: serial.Serial
event_listener = PacketEventListener()


def init():
    print("Initializing serial connection...")

    # ls /devでシリアル通信先を確認!!
    global ser
    ser = serial.Serial('/dev/ttyUSB0', 9600)
    if ser is None:
        print('Error')

    print("Starting serial receiver...")
    th = threading.Thread(target=await_packets())
    th.start()


def data_packet(packet: RaspberryPiPacket):
    ser.write(bytearray(packet.data))
    ser.flush()


def await_packets():
    while True:
        if ser.in_waiting <= 0:
            continue

        try:
            packet = ArduinoPacket(ser.read_all())
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


