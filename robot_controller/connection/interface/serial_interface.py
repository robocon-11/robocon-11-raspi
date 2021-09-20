import serial
from connection.interface.connection_interface import ConnectionInterface


class SerialInterface(ConnectionInterface):
    ser: serial.Serial

    def init(self):
        print("Using Serial Interface")

        # ls /devでシリアル通信先を確認!!
        self.ser = serial.Serial('/dev/ttyUSB0', 9600)
        if self.ser is None:
            print('\033[31m[ERROR] \033[0m/dev/ttyUSB0 is not found.')
            exit(1)

    def send_data(self, data: bytearray):
        self.ser.write(data)
        self.ser.flush()

    def read_data(self):
        return self.ser.read_all()

    def is_waiting(self):
        return self.ser.in_waiting <= 0
