from connection.output_packets import OutputPacket


class ConnectionInterface:
    def __init__(self):
        self.initialized = False  # Arduinoのシリアルポートが初期化されたかどうか
        self.sending_stopped = False  # Arduinoへのパケット送信が可能かどうか
        self.packet_queue: dict[int, OutputPacket] = {}  # パケットのキュー
        self.packet_key_queue: list[int] = []  # パケット（unique_id）のキュー
        self.last_updated_at = 0  # パケットを最後に送信した時間
        self.last_sent_packet_unique_id = -1  # 最後に送信したパケットのUnique ID
        self.packet_resent_count = 0  # 最後に送信したパケットを再送した数

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
