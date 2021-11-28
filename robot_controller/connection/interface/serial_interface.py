import serial
import logger
from connection.interface.connection_interface import ConnectionInterface


class SerialInterface(ConnectionInterface):
    ser: serial.Serial
    
    def __init__(self, host, name, baudrate=9600):
        super(SerialInterface, self).__init__()
        self.name = name
        self.host = host
        self.baudrate = baudrate

    def init(self):
        # ls /devでシリアル通信先を確認!!
        self.ser = serial.Serial(self.host, self.baudrate)

        if self.ser is None:
            logger.error("{} is not found.".format(self.host))
            exit(1)

        # self.ser.set_buffer_size(rx_size=4096, tx_size=4096)

    def send_data(self, data: bytearray):
        self.ser.write(data)
        self.ser.flush()

    def read_data(self):
        return self.ser.read_all()

    def is_waiting(self):
        return self.ser.in_waiting <= 0

    def get_name(self):
        return self.name
