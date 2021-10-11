from connection.output_packets import *


class ConnectionInterface:
    def init(self):
        pass

    def send_data(self, data):
        pass

    def read_data(self):
        pass

    def is_waiting(self):
        pass
