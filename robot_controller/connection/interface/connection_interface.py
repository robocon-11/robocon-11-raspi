from connection.output_packets import OutputPacket


class ConnectionInterface:
    def __init__(self):
        self.initialized = False  # Arduinoのシリアルポートが初期化されたかどうか
        self.sending_stopped = False  # Arduinoへのパケット送信が可能かどうか
        self.packet_queue: dict[int, OutputPacket] = {}  # パケットのキュー
        self.packet_key_queue: list[int] = []  # パケット（rand_id）のキュー

    def init(self):
        pass

    def send_data(self, data):
        pass

    def read_data(self):
        pass

    def is_waiting(self):
        pass

    def get_name(self):
        pass
