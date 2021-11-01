import threading
import time
import smbus2 as smbus


class LSM9D01:
    def _load(self):
        addressG = 0x6a
        addressA = 0x6a
        addressM = 0x1c
        getG = 0x18
        getA = 0x28
        getM = 0x28
        getTemp = 0x15

        CTRL_REG1_G = 0x10
        CTRL_REG4 = 0x1E
        CTRL_REG5_XL = 0x1F
        CTRL_REG3_M = 0x22

        bus = smbus.SMBus(1)

        bus.write_byte_data(addressG, CTRL_REG1_G, 0b00100000)  # gyro/accel odr and bw
        bus.write_byte_data(addressG, CTRL_REG4, 0b00111000)  # enable gyro axis
        bus.write_byte_data(addressA, CTRL_REG5_XL, 0b00111000)  # enable acceleromete
        bus.write_byte_data(addressM, CTRL_REG3_M, 0b00000000)  # enable mag continuous

        def alter(alterdata):
            return alterdata if alterdata < 32768 else alterdata - 65536

        # ジャイロ・加速度・磁気・温度センサの生データを取得して繰り返し表示
        while True:
            dataA = bus.read_i2c_block_data(addressA, getA, 6)
            rawAX = dataA[0] | dataA[1] << 8
            rawAY = dataA[2] | dataA[3] << 8
            rawAZ = dataA[4] | dataA[5] << 8
            AX = alter(rawAX)
            AY = alter(rawAY)
            AZ = alter(rawAZ)
            # print "AX:" + "%d" % AX + " ",
            # print "AY:" + "%d" % AY + " ",
            # print "AZ:" + "%d" % AZ + " "
            dataG = bus.read_i2c_block_data(addressG, getG, 6)
            rawGX = dataG[0] | dataG[1] << 8
            rawGY = dataG[2] | dataG[3] << 8
            rawGZ = dataG[4] | dataG[5] << 8
            GX = alter(rawGX)
            GY = alter(rawGY)
            GZ = alter(rawGZ)
            # print "GX: " + "%d" % GX + "",
            # print "GY: " + "%d" % GY + "",
            # print "GZ: " + "%d" % GZ + ""
            dataM = bus.read_i2c_block_data(addressM, getM, 6)
            rawMX = dataM[0] | dataM[1] << 8
            rawMY = dataM[2] | dataM[3] << 8
            rawMZ = dataM[4] | dataM[5] << 8
            MX = alter(rawMX)
            MY = alter(rawMY)
            MZ = alter(rawMZ)
            # print "MX:" + "%d" % MX + "",
            # print "MY:" + "%d" % MY + "",
            # print "MZ:" + "%d" % MZ + ""
            dataTemp = bus.read_i2c_block_data(addressG, getTemp, 2)
            rawTemp = dataTemp[0] | dataTemp[1] << 8
            # print "Temp:" + "%d" % rawTemp + "  "
            # print("---------------------------------------------")
            time.sleep(1)

    def __init__(self):
        # th = threading.Thread(target=self._load)
        # th.start()
        pass


# LSM9D01 = LSM9D01()
