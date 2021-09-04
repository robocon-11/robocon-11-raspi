import time
import arduino_manager
from sensor.sensor_mamager import SensorManager
from connection.arduino_to_rpi_packets import *
from connection.rpi_to_arduino_packets import *

STATE_WILL_BEGIN = 0  # 電源投入後
STATE_PHASE_1_STARTED = 1  # 1回目に左側のS/Bラインを超えた
STATE_PHASE_1_TURNED_CORNER_1 = 2  # スタート後1つめの角を曲がった
STATE_PHASE_1_TURNED_CORNER_2 = 3  # スタート後2つめの角を曲がった
STATE_PHASE_1_TURNED_CORNER_3 = 4  # スタート後3つめの角を曲がった
STATE_PHASE_1_TURNED_CORNER_4 = 5  # スタート後4つめの角を曲がった
STATE_PHASE_2_STARTED = 6  # 2回目に左側のS/Bラインを超えた
STATE_PHASE_2_TURNED_CORNER_1 = 7
STATE_PHASE_2_TURNED_CORNER_2 = 8
STATE_PHASE_2_TURNED_CORNER_3 = 9
STATE_PHASE_2_TURNED_CORNER_4 = 10
STATE_PHASE_3_STARTED = 11  # 3回目に左側のS/Bラインを超えた
STATE_PHASE_3_TURNED_CORNER_1 = 12
STATE_PHASE_3_TURNED_CORNER_2 = 13
STATE_FINISHED = 14  # 右側のS/Bラインを超えた

running = True
lost_ball = False

state = STATE_WILL_BEGIN
x = 0.0
y = 0.0

if __name__ == "__main__":
    arduino_manager.init()

    SensorManager()\
        .set_packet(MeasureNineAxisSensorPacket(1919))\
        .send()\
        .set_on_receive(lambda pk: on_sensor_manager_resulted(pk))


def on_sensor_manager_resulted(pk: NineAxisSensorResultPacket):
    if state == STATE_WILL_BEGIN:
        print("pid: " + pk.packet_id)

