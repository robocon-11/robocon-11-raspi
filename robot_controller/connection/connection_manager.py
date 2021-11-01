import threading
import time
import controller_board_manager
import core
import logger
from connection.input_packets import *
from connection.interface.serial_interface import SerialInterface
from connection.interface.udp_interface import UDPInterface
from connection.interface.internal_interface import InternalInterface
from connection.output_packets import OutputPacket
from connection.packet_event_listener import PacketEventListener

# 通信インターフェース
connection_interfaces: list = [SerialInterface()]

# パケット用イベントリスナ
event_listener = PacketEventListener()


# 初期化
def init():
    logger.info("Initializing connection interface...")
    for interface in connection_interfaces:
        interface.init()

    logger.info("Starting packet receiver...")
    for interface in connection_interfaces:
        th = threading.Thread(target=_await_packets, args=(interface,))
        th.start()

    logger.info("Starting packet sender...")
    th1 = threading.Thread(target=_send_packets)
    th1.start()


# SensorManagerを保持
def add_sensor_manager(rand_id, sensor_manager):
    event_listener.add_manager(rand_id, sensor_manager)


# キューにパケットを追加する
def data_packet(packet: OutputPacket):
    packet.encode()
    for interface in connection_interfaces:
        interface.packet_key_queue.insert(0, packet.rand_id)
        interface.packet_queue[packet.rand_id] = packet


# パケット送信のキューイング
def _send_packets():
    while core.running:
        for interface in connection_interfaces:
            if not interface.sending_stopped and not len(interface.packet_key_queue) == 0:
                rand_id = interface.packet_key_queue.pop()
                pk = interface.packet_queue[rand_id]
                _send_packet(interface, pk)
                time.sleep(0.01)  # 10ms待つ


# パケットを送信
def _send_packet(interface, pk):
    if core.debug:
        logger.send("(" + interface.get_name() + " / " + str(len(pk.data)) + ") " + str(pk.data))
    logger.state(str(core.instance.state))

    controller_board_manager.green_led_on()
    interface.send_data(pk.data)


# パケット受信待機
def _await_packets(interface):
    while core.running:
        if interface.is_waiting():
            continue

        controller_board_manager.blue_led_on()

        raw = interface.read_data()
        if raw is None:
            continue

        raw_hex = raw.hex()

        if core.debug:
            logger.receive("(" + interface.get_name() + " / " + str(len(raw)) + ") " + raw_hex)

        # 通信開始
        if (not interface.initialized) and bytearray("Transmission Start", encoding='utf8').hex() in raw_hex:
            interface.initialized = True
            event_listener.on_connection_start(interface)
            continue

        # データサイズエラー
        if "Invalid data size" in raw_hex:
            logger.error("(" + interface.get_name() + ") Invalid Data Size Error")
            continue

        # 受信データを\r\nで区切って処理
        split = str(raw_hex).split("0d0a")

        for text in split:
            array = bytearray.fromhex(text)
            print(text)
            string = ""

            try:
                string = array.decode(encoding='utf8')
            except UnicodeDecodeError:
                pass

            # パケット送信停止命令
            if string == "Stop":
                interface.sending_stopped = True
                logger.debug('(' + interface.get_name() + ') Stop')
                continue

            # 受信信号（rand_id）
            elif string.isdecimal() and len(string) == 4:
                interface.sending_stopped = False  # パケット送信停止解除
                del interface.packet_queue[int(string)]
                continue

            elif len(array) > InputPacket.PACKET_LENGTH:
                byte_ids = array[InputPacket.PACKET_LENGTH:]
                ids = [0, 0, 0, 0]
                i = 0
                for b in byte_ids:
                    ids[i] = str(int(b))
                    i = i + 1

                # キューからパケットを削除
                if len(ids) == 4:
                    interface.sending_stopped = False  # パケット送信停止解除
                    del interface.packet_queue[int("".join(ids))]

                _process_packet(array[0:InputPacket.PACKET_LENGTH - 1])

            elif len(array) == InputPacket.PACKET_LENGTH:
                _process_packet(array)

            # 予期しないパケットのとき
            else:
                logger.error("(" + interface.get_name() + ") Unexpected Packet Error (" + string + ")")
                continue


# 受信パケットの処理
def _process_packet(pk_data):
    try:
        packet = InputPacket(pk_data)
        packet.decode()

        if packet.packet_id == RightSteppingMotorAlertPacket.ID:
            pk = RightSteppingMotorAlertPacket(packet.data)
            pk.decode()
            event_listener.on_right_stepping_motor_alerted(pk)

        elif packet.packet_id == RightSteppingMotorFeedbackPacket.ID:
            pk = RightSteppingMotorFeedbackPacket(packet.data)
            pk.decode()
            event_listener.on_right_stepping_motor_feedback(pk)

        elif packet.packet_id == LeftSteppingMotorAlertPacket.ID:
            pk = LeftSteppingMotorAlertPacket(packet.data)
            pk.decode()
            event_listener.on_left_stepping_motor_alerted(pk)

        elif packet.packet_id == LeftSteppingMotorFeedbackPacket.ID:
            pk = LeftSteppingMotorFeedbackPacket(packet.data)
            pk.decode()
            event_listener.on_left_stepping_motor_feedback(pk)

        elif packet.packet_id == DistanceSensorResultPacket.ID:
            pk = DistanceSensorResultPacket(packet.data)
            pk.decode()
            event_listener.on_distance_sensor_resulted(pk)

        elif packet.packet_id == LineTracerResultPacket.ID:
            pk = LineTracerResultPacket(packet.data)
            pk.decode()
            event_listener.on_line_tracer_resulted(pk)

        elif packet.packet_id == NineAxisSensorResultPacket.ID:
            pk = NineAxisSensorResultPacket(packet.data)
            pk.decode()
            event_listener.on_nine_axis_sensor_resulted(pk)

        elif packet.packet_id == UpperServoMotorFeedbackPacket.ID:
            pk = UpperServoMotorFeedbackPacket(packet.data)
            pk.decode()
            event_listener.on_upper_servo_motor_feedback(pk)

        elif packet.packet_id == BottomServoMotorFeedbackPacket.ID:
            pk = BottomServoMotorFeedbackPacket(packet.data)
            pk.decode()

            event_listener.on_bottom_servo_motor_feedback(pk)

    except AssertionError as e:
        logger.error(e)
        return
