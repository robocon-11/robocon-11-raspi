import serial
from protocol.rpi_to_arduino_packets import Packet

MOTOR_LEFT = 0   # 左モータ
MOTOR_RIGHT = 1  # 右モータ

# ls /devでシリアル通信先を確認!!
serial = serial.Serial('/dev/ttyUSB0', 9600)
if serial is None:
    print('Error')


def data_packet(packet: Packet):
    serial.write(bytearray(packet.data))
