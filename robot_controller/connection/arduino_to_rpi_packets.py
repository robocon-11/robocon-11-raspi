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
        self.payload = []

    def decode_packet(self):
        pass

    def decode(self):
        assert len(self.data) == self.PACKET_LENGTH

        self.packet_id = int(str(self.data[0]) + str(self.data[1]))
        self.rand_id = int(str(self.data[2]) + str(self.data[3]) + str(self.data[4]) + str(self.data[5]))
        self.payload = self.data[6:42]

        assert len(self.payload) == self.DATA_LENGTH

        self.decode_packet()


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

    def __init__(self, data):
        super(DistanceSensorResultPacket, self).__init__(data)
        self.distance = -1.0  # 対面する壁からの距離(mm)

    def decode_packet(self):
        pass  # TODO


class LineTracerResultPacket(ArduinoPacket):
    ID = 50

    def __init__(self, data):
        super(LineTracerResultPacket, self).__init__(data)
        self.on_line = False

    def decode_packet(self):
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

    def __init__(self, data):
        super(NineAxisSensorResultPacket, self).__init__(data)



