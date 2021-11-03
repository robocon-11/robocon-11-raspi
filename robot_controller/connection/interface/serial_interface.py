import serial
import logger
from connection.interface.connection_interface import ConnectionInterface


class SerialInterface(ConnectionInterface):
    ser: serial.Serial
    
    def __init__(self):
        super(SerialInterface, self).__init__()

    def init(self):
        # ls /devでシリアル通信先を確認!!
        try:
            self.ser = serial.Serial('/dev/ttyUSB0', 9600)
        except FileNotFoundError:
            self.ser = serial.Serial('/dev/ttyUSB1', 9600)

        if self.ser is None:
            logger.error("/dev/ttyUSB0 is not found.")
            exit(1)

    def send_data(self, data: bytearray):
        self.ser.write(data)
        self.ser.flush()

    def read_data(self):
        return self.ser.read_all()

    def is_waiting(self):
        return self.ser.in_waiting <= 0

    def get_name(self):
        return "SerialInterface"
