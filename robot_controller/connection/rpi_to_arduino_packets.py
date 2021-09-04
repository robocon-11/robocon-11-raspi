# Raspberry Pi->Arduinoのパケット
class RaspberryPiPacket:
    ROTATE_RIGHT = 0  # 右回転
    ROTATE_LEFT = 1  # 左回転

    MOTOR_UNLOCKED = 0  # モータをロックしない
    MOTOR_LOCKED = 1  # モータをロックする

    DATA_TYPE_1 = 0  # 角速度+総角度
    DATA_TYPE_2 = 1  # 総角度+時間

    UNKNOWN_PACKET_ID = -1
    PACKET_LENGTH = 24  # 全パケット長
    DATA_SIZE = 8  # データ長

    # @arg _rand_id: ランダムな4bitの配列
    def __init__(self, _rand_id):
        self.data = []
        self.packet_id = self.UNKNOWN_PACKET_ID
        self.locked = self.MOTOR_UNLOCKED
        self.direction = self.ROTATE_RIGHT
        self.type = self.DATA_TYPE_1
        self.data_1 = [0 for _ in range(self.DATA_SIZE)]
        self.data_2 = [0 for _ in range(self.DATA_SIZE)]
        self._rand_id = _rand_id

    def encode(self):
        assert self.packet_id != self.UNKNOWN_PACKET_ID
        assert len(self.data_1) == self.DATA_SIZE
        assert len(self.data_2) == self.DATA_SIZE
        assert 1000 <= self._rand_id <= 9999

        self.data.append(self.packet_id)
        self.data.append(self._rand_id)
        self.data.append(self.locked)
        self.data.append(self.direction)
        self.data.append(self.type)
        self.data.extend(self.data_1)
        self.data.extend(self.data_2)

        assert len(self.data) == self.PACKET_LENGTH


class UpperServoMotorPacket(RaspberryPiPacket):
    ID = 0

    def __init__(self, _rand_id):
        super(UpperServoMotorPacket, self).__init__(_rand_id)


class BottomServoMotorPacket(RaspberryPiPacket):
    ID = 1

    def __init__(self, _rand_id):
        super(BottomServoMotorPacket, self).__init__(_rand_id)


class RightSteppingMotorPacket(RaspberryPiPacket):
    ID = 2

    def __init__(self, _rand_id):
        super(RightSteppingMotorPacket, self).__init__(_rand_id)


class LeftSteppingMotorPacket(RaspberryPiPacket):
    ID = 3

    def __init__(self, _rand_id):
        super(LeftSteppingMotorPacket, self).__init__(_rand_id)


class MeasureDistanceToBallPacket(RaspberryPiPacket):
    ID = 4

    def __init__(self, _rand_id):
        super(MeasureDistanceToBallPacket, self).__init__(_rand_id)


class MeasureLineTracerPacket(RaspberryPiPacket):
    ID = 5

    def __init__(self, _rand_id):
        super(MeasureLineTracerPacket, self).__init__(_rand_id)


class MeasureNineAxisSensorPacket(RaspberryPiPacket):
    ID = 6

    def __init__(self, _rand_id):
        super(MeasureNineAxisSensorPacket, self).__init__(_rand_id)

