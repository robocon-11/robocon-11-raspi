import struct


# Raspberry Pi->Arduinoのパケット
class OutputPacket:
    ROTATION_RIGHT = 0  # モータを右回転
    ROTATION_LEFT = 1  # モータを左回転
    ROTATION_LOCKED = 2  # ロック
    ROTATION_FORWARD = 3  # 左右のモータで前進
    ROTATION_BACK = 4  # 左右のモータで後進
    ROTATION_TURNING_RIGHT = 5  # 左右のモータで右旋回
    ROTATION_TURNING_LEFT = 6  # 左右のモータで左旋回

    MOTOR_UNLOCKED = 0  # モータをロックしない
    MOTOR_LOCKED = 1  # モータをロックする

    DATA_TYPE_1 = 0  # 角速度+総角度
    DATA_TYPE_2 = 1  # 総角度+時間
    DATA_TYPE_3 = 2  # 回転開始
    DATA_TYPE_4 = 3  # 回転停止

    UNKNOWN_PACKET_ID = -1
    PACKET_LENGTH = 24  # 全パケット長
    DATA_SIZE = 4  # データ長

    # @arg _unique_id: ランダムな4bitの配列
    def __init__(self, _unique_id):
        self.data = []
        self.packet_id: int = self.UNKNOWN_PACKET_ID
        self.direction: int = self.ROTATION_RIGHT
        self.type: int = self.DATA_TYPE_1
        self.data_1 = [0x00 for _ in range(self.DATA_SIZE)]
        self.data_2 = [0x00 for _ in range(self.DATA_SIZE)]
        self.data_3 = [0x00 for _ in range(self.DATA_SIZE)]
        self.data_4 = [0x00 for _ in range(self.DATA_SIZE)]
        self.unique_id: int = _unique_id

    def encode_packet(self):
        pass

    def encode(self):
        assert len(self.data_1) == self.DATA_SIZE
        assert len(self.data_2) == self.DATA_SIZE
        assert len(self.data_3) == self.DATA_SIZE
        assert len(self.data_4) == self.DATA_SIZE

        self.encode_packet()

        self.data.extend(self.packet_id.to_bytes(2, byteorder='big'))
        self.data.extend(self.unique_id.to_bytes(4, byteorder='big'))
        self.data.append(bytes([self.direction])[0])
        self.data.append(bytes([self.type])[0])
        self.data.extend(self.data_1)
        self.data.extend(self.data_2)
        self.data.extend(self.data_3)
        self.data.extend(self.data_4)

    def decode_packet(self):
        pass

    def decode(self):
        self.packet_id = int.from_bytes(self.data[0:2], byteorder='big')
        self.unique_id = int.from_bytes(self.data[2:6], byteorder='big')
        self.direction = int(self.data[6])
        self.type = int(self.data[7])
        self.data_1 = self.data[8:12]
        self.data_2 = self.data[12:16]
        self.data_3 = self.data[16:20]
        self.data_4 = self.data[20:24]

        self.decode_packet()


def float_to_array(f):
    return struct.pack(">f", f)


def array_to_float(array):
    return struct.unpack('>f', bytes(array))[0]


class RightSteppingMotorPacket(OutputPacket):
    ID = 10

    def __init__(self, _unique_id):
        super(RightSteppingMotorPacket, self).__init__(_unique_id)
        self.packet_id = self.ID
        self.value_1: float = 0.0
        self.value_2: float = 0.0

    def encode_packet(self):
        self.data_1 = float_to_array(self.value_1)
        self.data_2 = float_to_array(self.value_2)

    def decode_packet(self):
        self.value_1 = array_to_float(self.data_1)
        self.value_2 = array_to_float(self.data_2)


class LeftSteppingMotorPacket(OutputPacket):
    ID = 20

    def __init__(self, _unique_id):
        super(LeftSteppingMotorPacket, self).__init__(_unique_id)
        self.packet_id = self.ID
        self.value_1: float = 0.0
        self.value_2: float = 0.0

    def encode_packet(self):
        self.data_1 = float_to_array(self.value_1)
        self.data_2 = float_to_array(self.value_2)

    def decode_packet(self):
        self.value_1 = array_to_float(self.data_1)
        self.value_2 = array_to_float(self.data_2)


class BothSteppingMotorPacket(OutputPacket):
    ID = 30

    def __init__(self, _unique_id):
        super(BothSteppingMotorPacket, self).__init__(_unique_id)
        self.packet_id = self.ID
        self.value_1: float = 0.0  # 右モータのデータ1
        self.value_2: float = 0.0  # 右モータのデータ2
        self.value_3: float = 0.0  # 左モータのデータ1
        self.value_4: float = 0.0  # 左モータのデータ2

    def encode_packet(self):
        self.data_1 = float_to_array(self.value_1)
        self.data_2 = float_to_array(self.value_2)
        self.data_3 = float_to_array(self.value_3)
        self.data_4 = float_to_array(self.value_4)

    def decode_packet(self):
        self.value_1 = array_to_float(self.data_1)
        self.value_2 = array_to_float(self.data_2)
        self.value_3 = array_to_float(self.data_3)
        self.value_4 = array_to_float(self.data_4)


class MeasureDistancePacket(OutputPacket):
    ID = 40

    def __init__(self, _unique_id):
        super(MeasureDistancePacket, self).__init__(_unique_id)
        self.packet_id = self.ID


class MeasureLineTracerPacket(OutputPacket):
    ID = 50

    def __init__(self, _unique_id):
        super(MeasureLineTracerPacket, self).__init__(_unique_id)
        self.packet_id = self.ID


class UpperServoMotorPacket(OutputPacket):
    ID = 60

    def __init__(self, _unique_id):
        super(UpperServoMotorPacket, self).__init__(_unique_id)
        self.packet_id = self.ID


class BottomServoMotorPacket(OutputPacket):
    ID = 70

    def __init__(self, _unique_id):
        super(BottomServoMotorPacket, self).__init__(_unique_id)
        self.packet_id = self.ID


class MeasureNineAxisSensorPacket(OutputPacket):
    ID = 80

    def __init__(self, _unique_id):
        super(MeasureNineAxisSensorPacket, self).__init__(_unique_id)
        self.packet_id = self.ID
