import threading
import time

import controller_board_manager
import core
import logger
from connection.input_packets import *
from connection.interface.serial_interface import ConnectionInterface
from connection.interface.serial_interface import SerialInterface
from connection.output_packets import OutputPacket
from connection.packet_event_listener import PacketEventListener

# 通信インターフェース
connection_interfaces: list = [SerialInterface()]

# パケット用イベントリスナ
event_listener = PacketEventListener()

CONNECTION_TIME_OUT = 3  # s


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
def add_sensor_manager(unique_id, sensor_manager):
    event_listener.add_manager(unique_id, sensor_manager)


# キューにパケットを追加する
def data_packet(packet: OutputPacket):
    packet.encode()
    for interface in connection_interfaces:
        interface.packet_key_queue.insert(0, packet.unique_id)
        interface.packet_queue[packet.unique_id] = packet


# パケット送信のキューイング
def _send_packets():
    while core.running:
        for interface in connection_interfaces:
            if not interface.sending_stopped and not len(interface.packet_key_queue) == 0:
                unique_id = interface.packet_key_queue.pop()
                pk = interface.packet_queue[unique_id]
                _send_packet(interface, pk, True)
                time.sleep(0.1)  # 10ms待つ


# パケットを送信
def _send_packet(interface: ConnectionInterface, pk: OutputPacket, update_time=False):
    if core.debug:
        logger.send(
            "(" + interface.get_name() + " / " + str(len(pk.data)) + " / " + str(pk.unique_id) + ") " + bytes(pk.data).hex())
    logger.state(str(core.instance.state))

    controller_board_manager.green_led_on()

    interface.send_data(pk.data)
    interface.sending_stopped = True

    # logger.debug('(' + interface.get_name() + ') Stop')
    if update_time:
        interface.last_sent_packet_unique_id = pk.unique_id
        interface.last_updated_at = time.time()


# パケット受信待機
def _await_packets(interface: ConnectionInterface):
    buffer = []

    while core.running:
        # パケットを送信してCONNECTION_TIME_OUT(ms)以内に受信通知が来なかった場合
        if interface.sending_stopped and time.time() - interface.last_updated_at > CONNECTION_TIME_OUT:
            # パケットの再送を5回以上行ったら...
            if interface.packet_resent_count > 5:
                controller_board_manager.red_led_on()
                logger.error("Tried sending packet (Unique ID/PacketID: {}/{}) to {} for {} times, but could not "
                             "receive the signal 'Stop'.".format(str(interface.last_sent_packet_unique_id), str(
                    interface.packet_queue[interface.last_sent_packet_unique_id].packet_id), interface.get_name(),
                                                                 str(interface.packet_resent_count)))

            _send_packet(interface, interface.packet_queue[interface.last_sent_packet_unique_id])  # 再送する
            interface.packet_resent_count += 1

        if interface.is_waiting():
            continue

        controller_board_manager.blue_led_on()

        raw = interface.read_data()
        if raw is None:
            continue

        raw_hex = raw.hex()

        if core.debug:
            logger.receive("(" + interface.get_name() + " / " + str(len(raw)) + ") " + raw_hex)
            # logger.debug("(" + interface.get_name() + " / " + str(len(raw)) + ") " + str(raw, encoding='utf-8'))

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
            string = ""

            try:
                string = array.decode(encoding='utf8')
            except UnicodeDecodeError:
                pass

            # パケット送信停止命令
            if string.startswith('>'):
                logger.debug_i('(' + interface.get_name() + ') ' + string)
                continue

            elif len(array) == 0:
                continue

            # 受信信号（unique_id）
            elif len(array) == 4:
                interface.sending_stopped = False  # パケット送信停止解除
                interface.last_updated_at = time.time()  # interfaceの最終更新時間を更新
                interface.packet_resent_count = 0  # 再送回数を0に
                unique_id = int.from_bytes(array, byteorder='big')
                logger.debug("receive: " + str(unique_id))
                del interface.packet_queue[unique_id]
                continue

            elif len(array) == InputPacket.PACKET_LENGTH - 10:
                buffer.extend(array)

            elif len(buffer) == InputPacket.PACKET_LENGTH - 10 and len(array) == 10:
                buffer.extend(array)
                _process_packet(buffer)
                buffer = []

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
