import struct


# Raspberry Pi->Arduinoのパケット
class InputPacket:
    PACKET_LENGTH = 42  # 全パケット長
    DATA_LENGTH = 36  # データ長

    UNKNOWN_PACKET_ID = -1
    UNKNOWN_UNIQUE_ID = -1

    def __init__(self, data: list):
        self.data: list = data
        self.packet_id = self.UNKNOWN_PACKET_ID
        self.unique_id = self.UNKNOWN_UNIQUE_ID
        self.payload = [[0x00 for _ in range(4)] for _ in range(9)]

    def decode_packet(self):
        pass

    def decode(self):
        assert len(self.data) == self.PACKET_LENGTH

        self.packet_id = int.from_bytes(self.data[0:2], byteorder='big')
        self.unique_id = int.from_bytes(self.data[2:6], byteorder='big')

        for i in range(0, 9):
            index = i * 4 + 6
            self.payload[i] = [self.data[index], self.data[index + 1], self.data[index + 2], self.data[index + 3]]

        self.decode_packet()

    def encode_packet(self):
        pass

    def encode(self):
        self.encode_packet()

        self.data.extend(self.packet_id.to_bytes(2, byteorder='big'))
        self.data.extend(self.unique_id.to_bytes(4, byteorder='big'))

        for p in self.payload:
            self.data.extend(p)


def array_to_float(array):
    return struct.unpack('<f', bytes(array))[0]


def float_to_array(f):
    return struct.pack("<f", f)


class RightSteppingMotorAlertPacket(InputPacket):
    ID = 10

    def __init__(self, data):
        super(RightSteppingMotorAlertPacket, self).__init__(data)
        self.packet_id = self.ID


class RightSteppingMotorFeedbackPacket(InputPacket):
    ID = 11

    def __init__(self, data):
        super(RightSteppingMotorFeedbackPacket, self).__init__(data)
        self.packet_id = self.ID


class LeftSteppingMotorAlertPacket(InputPacket):
    ID = 20

    def __init__(self, data):
        super(LeftSteppingMotorAlertPacket, self).__init__(data)
        self.packet_id = self.ID


class LeftSteppingMotorFeedbackPacket(InputPacket):
    ID = 21

    def __init__(self, data):
        super(LeftSteppingMotorFeedbackPacket, self).__init__(data)
        self.packet_id = self.ID


class BothSteppingMotorAlertPacket(InputPacket):
    ID = 30

    def __init__(self, data):
        super(BothSteppingMotorAlertPacket, self).__init__(data)
        self.packet_id = self.ID


class BothSteppingMotorFeedbackPacket(InputPacket):
    ID = 31

    def __init__(self, data):
        super(BothSteppingMotorFeedbackPacket, self).__init__(data)
        self.packet_id = self.ID


class DistanceSensorResultPacket(InputPacket):
    ID = 40
    distance = 0.0  # 対面する壁からの距離(mm)

    def __init__(self, data):
        super(DistanceSensorResultPacket, self).__init__(data)
        self.packet_id = self.ID

    def decode_packet(self):
        self.distance = array_to_float(self.payload[0])


class LineTracerResultPacket(InputPacket):
    ID = 50
    is_on_line = False  # ライン上かどうか

    def __init__(self, data):
        super(LineTracerResultPacket, self).__init__(data)
        self.packet_id = self.ID
        self.is_on_line = False

    def decode_packet(self):
        if self.payload[0][3] == 0x01:
            self.is_on_line = True
        pass  # TODO


class UpperServoMotorFeedbackPacket(InputPacket):
    ID = 60

    def __init__(self, data):
        super(UpperServoMotorFeedbackPacket, self).__init__(data)
        self.packet_id = self.ID


class BottomServoMotorFeedbackPacket(InputPacket):
    ID = 70

    def __init__(self, data):
        super(BottomServoMotorFeedbackPacket, self).__init__(data)
        self.packet_id = self.ID


class NineAxisSensorResultPacket(InputPacket):
    ID = 80
    geomagnetism = 0.0  # 地磁気

    def __init__(self, data):
        super(NineAxisSensorResultPacket, self).__init__(data)
        self.packet_id = self.ID

    def decode_packet(self):
        self.geomagnetism = array_to_float(self.payload[8])

    def encode_packet(self):
        self.payload[0] = float_to_array(self.geomagnetism)


