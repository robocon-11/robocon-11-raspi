class Packet:

    ROTATE_RIGHT = 0b00    # 右回転
    ROTATE_LEFT = 0b01     # 左回転

    MOTOR_UNLOCKED = 0b00  # モータをロックしない
    MOTOR_LOCKED = 0b01    # モータをロックする

    DATA_TYPE_1 = 0b00     # 角速度+総角度
    DATA_TYPE_2 = 0b01     # 総角度+時間

    def __init__(self):
        self.data = []
        self.packet_id = []
        self.locked = self.MOTOR_UNLOCKED
        self.direction = self.ROTATE_RIGHT
        self.type = self.DATA_TYPE_1
        self.data_1 = [0b00 for _ in range(16)]
        self.data_2 = [0b00 for _ in range(16)]

    def encode(self):
        assert len(self.data_1) == 16
        assert len(self.data_2) == 16

        self.data.extend(self.packet_id)
        self.data.append(self.locked)
        self.data.append(self.direction)
        self.data.append(self.type)
        self.data.extend(self.data_1)
        self.data.extend(self.data_2)

        assert len(self.data) == 37


class UpperServoMotorPacket(Packet):
    def __init__(self):
        super(UpperServoMotorPacket, self).__init__()
        self.packet_id = [0b00, 0b00]


class BottomServoMotorPacket(Packet):
    def __init__(self):
        super(BottomServoMotorPacket, self).__init__()
        self.packet_id = [0b00, 0b01]


class RightSteppingMotorPacket(Packet):
    def __init__(self):
        super(RightSteppingMotorPacket, self).__init__()
        self.packet_id = [0b01, 0b00]


class LeftSteppingMotorPacket(Packet):
    def __init__(self):
        super(LeftSteppingMotorPacket, self).__init__()
        self.packet_id = [0b01, 0b01]

