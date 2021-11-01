import logger
from connection.interface.connection_interface import ConnectionInterface
from connection.output_packets import *
from sensor.lsm9d01_manager import LSM9D01


class InternalInterface(ConnectionInterface):

    def __init__(self):
        super(InternalInterface, self).__init__()

    def init(self):
        pass

    def send_data(self, data: bytearray):
        pk = OutputPacket(data)
        pk.decode()

        if pk.packet_id == MeasureNineAxisSensorPacket.ID:
            pass

        self.received_packets.insert(0, pk)

    def read_data(self):
        pass

    def is_waiting(self):
        return False

    def get_name(self):
        return "InternalInterface"
