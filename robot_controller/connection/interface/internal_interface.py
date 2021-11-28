import logger
import core
from threading import Thread
from device_driver import motor_driver
from connection.interface.connection_interface import ConnectionInterface
from connection.input_packets import *
from connection.output_packets import *


class InternalInterface(ConnectionInterface):

    def __init__(self):
        super(InternalInterface, self).__init__()
        self.send_packet_queue = []
        self.received_packets = []
        Thread(target=self._process_packets).start()

    def init(self):
        self.put_data(bytearray("Transmission Start", encoding='utf8'))

    # パケットを受信したとき
    def _receive_data(self, pk: OutputPacket):
        self.received_packets.insert(0, pk)

    # 受信したパケットを処理する
    def _process_packets(self):
        while True:
            if len(self.received_packets) == 0:
                continue

            pk = self.received_packets.pop()
            if pk.packet_id == BothSteppingMotorPacket.ID:
                pass

            elif pk.packet_id == LeftSteppingMotorPacket.ID:
                pass

            elif pk.packet_id == RightSteppingMotorPacket.ID:
                pass

            elif pk.packet_id == MeasureNineAxisSensorPacket.ID:
                send_pk = NineAxisSensorResultPacket([])
                send_pk.unique_id = pk.unique_id
                send_pk.encode()
                self.put_data(bytes(send_pk.data))

            elif pk.packet_id == MeasureLineTracerPacket.ID:
                pass

            elif pk.packet_id == MeasureDistancePacket.ID:
                pass

    def put_data(self, data):
        self.send_packet_queue.insert(0, data)
        self.send_packet_queue.insert(0, bytes([0x0d, 0x0a]))

    # override
    def send_data(self, data: bytearray):
        pk = OutputPacket(0)
        pk.data = data
        pk.decode()
        self._receive_data(pk)
        self.put_data(pk.unique_id.to_bytes(4, byteorder='big'))

    # override
    def read_data(self):
        return self.send_packet_queue.pop()

    # override
    def is_waiting(self):
        return len(self.send_packet_queue) == 0

    # override
    def get_name(self):
        return "Internal"
