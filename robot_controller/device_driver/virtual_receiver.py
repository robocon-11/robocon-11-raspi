from threading import Thread

import core
from connection.interface.internal_interface import InternalInterface
from connection.output_packets import *


class VirtualReceiver:
    def __init__(self, interface: InternalInterface):
        self.interface = interface
        self.packet_queue = []

        th = Thread(target=self._process_packets)
        th.start()

    def receive_data(self, pk: OutputPacket):
        self.packet_queue.insert(0, pk)

    def _process_packets(self):
        while core.running:
            if len(self.packet_queue) == 0:
                continue

            pk = self.packet_queue.pop()
            if pk.packet_id == BothSteppingMotorPacket.ID:
                pass

            elif pk.packet_id == LeftSteppingMotorPacket.ID:
                pass

            elif pk.packet_id == RightSteppingMotorPacket.ID:
                pass

            elif pk.packet_id == MeasureNineAxisSensorPacket.ID:
                pass

            elif pk.packet_id == MeasureNineAxisSensorPacket.ID:
                pass

            elif pk.packet_id == MeasureLineTracerPacket.ID:
                pass

            elif pk.packet_id == MeasureDistancePacket.ID:
                pass
