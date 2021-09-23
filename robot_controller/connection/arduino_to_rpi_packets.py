import struct


# Raspberry Pi->Arduinoのパケット
class ArduinoPacket:
    PACKET_LENGTH = 42  # 全パケット長
    DATA_LENGTH = 36  # データ長

    UNKNOWN_PACKET_ID = -1
    UNKNOWN_RANDOM_ID = -1

    def __init__(self, data):
        self.data = data
        self.packet_id = self.UNKNOWN_PACKET_ID
        self.rand_id = self.UNKNOWN_RANDOM_ID
        self.payload = [
            [0x00, 0x00, 0x00, 0x00],
            [0x00, 0x00, 0x00, 0x00],
            [0x00, 0x00, 0x00, 0x00],
            [0x00, 0x00, 0x00, 0x00],
            [0x00, 0x00, 0x00, 0x00],
            [0x00, 0x00, 0x00, 0x00],
            [0x00, 0x00, 0x00, 0x00],
            [0x00, 0x00, 0x00, 0x00],
            [0x00, 0x00, 0x00, 0x00]
        ]

    def decode_packet(self):
        pass

    def decode(self):
        assert len(self.data) == self.PACKET_LENGTH

        self.packet_id = int(str(int(self.data[0])) + str(int(self.data[1])))
        self.rand_id = int(str(int(self.data[2])) + str(int(self.data[3])) + str(int(self.data[4])) + str(int(self.data[5])))

        for i in range(0, 9):
            index = i * 4 + 6
            self.payload[i] = [self.data[index], self.data[index + 1], self.data[index + 2], self.data[index + 3]]

        self.decode_packet()


def array_to_float(array):
    return struct.unpack('>f', bytes(array))[0]


class RightSteppingMotorAlertPacket(ArduinoPacket):
    ID = 10

    def __init__(self, data):
        super(RightSteppingMotorAlertPacket, self).__init__(data)


class RightSteppingMotorFeedbackPacket(ArduinoPacket):
    ID = 11

    def __init__(self, data):
        super(RightSteppingMotorFeedbackPacket, self).__init__(data)


class LeftSteppingMotorAlertPacket(ArduinoPacket):
    ID = 20

    def __init__(self, data):
        super(LeftSteppingMotorAlertPacket, self).__init__(data)


class LeftSteppingMotorFeedbackPacket(ArduinoPacket):
    ID = 21

    def __init__(self, data):
        super(LeftSteppingMotorFeedbackPacket, self).__init__(data)


class BothSteppingMotorAlertPacket(ArduinoPacket):
    ID = 30

    def __init__(self, data):
        super(BothSteppingMotorAlertPacket, self).__init__(data)


class BothSteppingMotorFeedbackPacket(ArduinoPacket):
    ID = 31

    def __init__(self, data):
        super(BothSteppingMotorFeedbackPacket, self).__init__(data)


class DistanceSensorResultPacket(ArduinoPacket):
    ID = 40
    distance = 0.0  # 対面する壁からの距離(mm)

    def __init__(self, data):
        super(DistanceSensorResultPacket, self).__init__(data)

    def decode_packet(self):
        self.distance = array_to_float(self.payload[0])


class LineTracerResultPacket(ArduinoPacket):
    ID = 50
    is_on_line = False  # ライン上かどうか

    def __init__(self, data):
        super(LineTracerResultPacket, self).__init__(data)
        self.on_line = False

    def decode_packet(self):
        if self.payload[0][3] == 0x01:
            self.is_on_line = True
        pass  # TODO


class UpperServoMotorFeedbackPacket(ArduinoPacket):
    ID = 60

    def __init__(self, data):
        super(UpperServoMotorFeedbackPacket, self).__init__(data)


class BottomServoMotorFeedbackPacket(ArduinoPacket):
    ID = 70

    def __init__(self, data):
        super(BottomServoMotorFeedbackPacket, self).__init__(data)


class NineAxisSensorResultPacket(ArduinoPacket):
    ID = 80
    geomagnetism = 0.0  # 地磁気

    def __init__(self, data):
        super(NineAxisSensorResultPacket, self).__init__(data)

    def decode_packet(self):
        self.geomagnetism = array_to_float(self.payload[8])



