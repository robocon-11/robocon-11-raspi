# Raspberry Pi->Arduinoのパケット
class OutputPacket:
    ROTATE_RIGHT_FORWARD = 0  # 右回転or前進
    ROTATE_LEFT_RETURN = 1  # 左回転or後進
    ROTATE_LOCKED = 2  # ロック

    MOTOR_UNLOCKED = 0  # モータをロックしない
    MOTOR_LOCKED = 1  # モータをロックする

    DATA_TYPE_1 = 0  # 角速度+総角度
    DATA_TYPE_2 = 1  # 総角度+時間
    DATA_TYPE_3 = 2  # 回転開始
    DATA_TYPE_4 = 3  # 回転停止

    UNKNOWN_PACKET_ID = -1
    PACKET_LENGTH = 16  # 全パケット長
    DATA_SIZE = 4  # データ長

    # @arg _rand_id: ランダムな4bitの配列
    def __init__(self, _rand_id):
        self.data = []
        self.packet_id = self.UNKNOWN_PACKET_ID
        self.direction = self.ROTATE_RIGHT_FORWARD
        self.type = self.DATA_TYPE_1
        self.data_1 = [0x00 for _ in range(self.DATA_SIZE)]
        self.data_2 = [0x00 for _ in range(self.DATA_SIZE)]
        self.rand_id = _rand_id

    def encode(self):
        assert len(self.data_1) == self.DATA_SIZE
        assert len(self.data_2) == self.DATA_SIZE

        self.data.extend([bytes([int(x)])[0] for x in str(self.packet_id)])
        self.data.extend([bytes([int(x)])[0] for x in str(self.rand_id)])
        self.data.append(bytes([self.direction])[0])
        self.data.append(bytes([self.type])[0])
        self.data.extend(self.data_1)
        self.data.extend(self.data_2)


class RightSteppingMotorPacket(OutputPacket):
    ID = 10

    def __init__(self, _rand_id):
        super(RightSteppingMotorPacket, self).__init__(_rand_id)
        self.packet_id = self.ID


class LeftSteppingMotorPacket(OutputPacket):
    ID = 20

    def __init__(self, _rand_id):
        super(LeftSteppingMotorPacket, self).__init__(_rand_id)
        self.packet_id = self.ID


class BothSteppingMotorPacket(OutputPacket):
    ID = 30

    def __init__(self, _rand_id):
        super(BothSteppingMotorPacket, self).__init__(_rand_id)
        self.packet_id = self.ID


class MeasureDistanceToBallPacket(OutputPacket):
    ID = 40

    def __init__(self, _rand_id):
        super(MeasureDistanceToBallPacket, self).__init__(_rand_id)
        self.packet_id = self.ID


class MeasureLineTracerPacket(OutputPacket):
    ID = 50

    def __init__(self, _rand_id):
        super(MeasureLineTracerPacket, self).__init__(_rand_id)
        self.packet_id = self.ID


class UpperServoMotorPacket(OutputPacket):
    ID = 60

    def __init__(self, _rand_id):
        super(UpperServoMotorPacket, self).__init__(_rand_id)
        self.packet_id = self.ID


class BottomServoMotorPacket(OutputPacket):
    ID = 70

    def __init__(self, _rand_id):
        super(BottomServoMotorPacket, self).__init__(_rand_id)
        self.packet_id = self.ID


class MeasureNineAxisSensorPacket(OutputPacket):
    ID = 80

    def __init__(self, _rand_id):
        super(MeasureNineAxisSensorPacket, self).__init__(_rand_id)
        self.packet_id = self.ID
