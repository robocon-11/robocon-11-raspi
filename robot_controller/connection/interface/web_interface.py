import logger
from flask import Flask
from connection.interface.connection_interface import ConnectionInterface
from connection.output_packets import *
from sensor.lsm9d01_manager import LSM9D01
from threading import Thread
from flask_classy import FlaskView


class WebInterface(ConnectionInterface, FlaskView):
    def send_data(self, data: bytearray):
        pk = OutputPacket(data)
        pk.decode()

        if pk.packet_id == MeasureNineAxisSensorPacket.ID:
            pass

        self.received_packets.insert(0, pk)

    def read_data(self):
        return self.packet_queue.pop()

    def is_waiting(self):
        return len(self.packet_queue) != 0

    def get_name(self):
        return "Web"

    def _update(self):
        while True:
            if len(self.packet_queue) != 0:
                pk = self.packet_queue.pop()

    def index(self):
        return "hello"

    def __init__(self):
        super(WebInterface, self).__init__()
        self.received_packets = []
        self.packet_queue = []
        self.app = Flask(self.__class__.__name__)

        WebInterface.register(self.app)
        Thread(target=self.app.run).start()

    def init(self):
        pass