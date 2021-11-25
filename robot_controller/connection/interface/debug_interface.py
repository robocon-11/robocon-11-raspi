
import logger
from connection.interface.connection_interface import ConnectionInterface
from connection.output_packets import *
from connection.input_packets import *
from sensor.lsm9d01_manager import LSM9D01
from threading import Thread


class DebugInterface(ConnectionInterface):

    def __init__(self):
        super(DebugInterface, self).__init__()
        self._packet_queue = []

    def init(self):
        pass

    def _send_bytearray(self, data):
        self._packet_queue.insert(0, data)

    def _on_receive_packet(self, pk: OutputPacket):
        if pk.packet_id == MeasureNineAxisSensorPacket.ID:
            p = NineAxisSensorResultPacket([])
            p.unique_id = pk.unique_id
            p.geomagnetism = 0.2
            p.encode()
            self._send_bytearray(p.data)

        elif pk.packet_id == BothSteppingMotorPacket.ID:
            # TODO
            pass

    def send_data(self, data: bytearray):
        pk = OutputPacket(data)
        pk.decode()
        self._send_bytearray(pk.unique_id.to_bytes(4, byteorder='big'))
        self._on_receive_packet(pk)

    def read_data(self):
        if not self.initialized:
            return bytearray('Transmission Start', encoding='utf8')

        return self._packet_queue.pop()

    def is_waiting(self):
        return not self.initialized or len(self._packet_queue) == 0

    def get_name(self):
        return "Internal"
