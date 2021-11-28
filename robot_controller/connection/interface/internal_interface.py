import logger
from connection.interface.connection_interface import ConnectionInterface
from connection.output_packets import *
from sensor.lsm9d01_manager import LSM9D01
from threading import Thread
from device_driver.virtual_receiver import VirtualReceiver


class InternalInterface(ConnectionInterface):

    def __init__(self):
        super(InternalInterface, self).__init__()
        self.packet_queue = []
        self.receiver = VirtualReceiver(self)

    def init(self):
        pass

    def put_data(self, data):
        self.packet_queue.insert(0, data)

    def send_data(self, data: bytearray):
        pk = OutputPacket(data)
        pk.decode()
        self.receiver.receive_data(pk)
        self.put_data(pk.unique_id.to_bytes(4, byteorder='big'))

    def read_data(self):
        return self.packet_queue.pop()

    def is_waiting(self):
        return len(self.packet_queue) == 0

    def get_name(self):
        return "Internal"
