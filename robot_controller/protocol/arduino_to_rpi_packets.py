class Packet:

    def __init__(self):
        self.data = []
        self.packet_id = []
        self.data_1 = []
        self.data_2 = []

    def decode(self):
        assert len(self.data) == 35

        self.packet_id = self.data[0:3]
        self.data_1 = self.data[3:19]
        self.data_2 = self.data[18:35]
