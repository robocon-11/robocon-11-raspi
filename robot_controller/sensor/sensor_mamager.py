from connection.arduino_to_rpi_packets import ArduinoPacket
from connection import connection_manager


class SensorManager:

    def __init__(self):
        self.__on_receive__ = None
        self.packet = None

    def on_receive(self, packet: ArduinoPacket):
        self.__on_receive__(packet)

    def send(self):
        connection_manager.add_sensor_manager(self.packet.rand_id, self)
        connection_manager.data_packet(self.packet)
        return self

    def set_packet(self, packet):
        self.packet = packet
        return self

    def set_on_receive(self, expression):
        self.__on_receive__ = expression
        return self
