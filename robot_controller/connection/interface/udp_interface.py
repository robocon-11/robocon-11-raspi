import logger
from socket import *
from connection.interface.connection_interface import ConnectionInterface
from connection.input_packets import InputPacket


class UDPInterface(ConnectionInterface):
    socket: socket

    def __init__(self, dest_ip, dest_port, name):
        super(UDPInterface, self).__init__()
        self.sender_ip = "172.20.1.1"
        self.sender_port = 4321
        self.sender_address = (self.sender_ip, self.sender_port)
        self.dest_ip = dest_ip  # w -iで確認
        self.dest_port = dest_port
        self.dest_address = (self.dest_ip, self.dest_port)
        self.name = name

    def init(self):
        self.socket = socket(AF_INET, SOCK_DGRAM)
        self.socket.bind(self.sender_address)

    def send_data(self, data: bytearray):
        self.socket.sendto(bytes(data), self.dest_address)

    def read_data(self):
        data, address = self.socket.recvfrom(InputPacket.PACKET_LENGTH)
        return data

    def is_waiting(self):
        return False

    def get_name(self):
        return self.name
