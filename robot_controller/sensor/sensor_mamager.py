from connection.input_packets import InputPacket
from connection import connection_manager


class SensorManager:

    def __init__(self):
        self.__on_receive__ = None
        self.packet = None

    # セットしたパケットに対する応答が返ってきたときに発火
    def on_receive(self, packet: InputPacket):
        self.__on_receive__(packet)

    # セットしたパケットを送信
    def send(self):
        connection_manager.add_sensor_manager(self.packet.rand_id, self)
        connection_manager.data_packet(self.packet)
        return self

    # パケットをセット
    def set_packet(self, packet):
        self.packet = packet
        return self

    # 応答時に発火させる関数をセット
    def set_on_receive(self, expression):
        self.__on_receive__ = expression
        return self
