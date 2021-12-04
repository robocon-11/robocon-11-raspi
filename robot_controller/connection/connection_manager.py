import threading
import time
import json
import controller_board_manager
import core
import logger
from connection.input_packets import *
from connection.interface.connection_interface import ConnectionInterface
from connection.interface.serial_interface import SerialInterface
from connection.interface.udp_interface import UDPInterface
from connection.interface.internal_interface import InternalInterface
from connection.output_packets import *
from connection.input_packets import *
from connection.packet_event_listener import PacketEventListener

# 通信インターフェース
# UDPInterface("172.20.1.137", 1234, "UDP"), SerialInterface(host="/dev/ttyUSB0", name="M5Stack", baudrate=115200)
connection_interfaces: list = [InternalInterface(), SerialInterface(host="/dev/ttyUSB0", name="Arduino", baudrate=115200)]

event_listener = PacketEventListener()  # パケット用イベントリスナ
received_packets = {}  # 受信したパケットのキュー
CONNECTION_TIME_OUT = 10  # sec


# 初期化
def init():
    logger.info("Initializing connection interface...")
    for interface in connection_interfaces:
        interface.init()

    logger.info("Starting packet sender...")
    th1 = threading.Thread(target=_send_packets)
    th1.start()

    logger.info("Starting packet receiver...")
    th0 = threading.Thread(target=_process_packets)
    th0.start()

    for interface in connection_interfaces:
        th = threading.Thread(target=_await_packets, args=(interface,))
        th.start()


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
                # time.sleep(0.001)  # 10ms待つ


# パケットを送信
def _send_packet(interface: ConnectionInterface, pk: OutputPacket, update_time=False):
    if core.debug:
        logger.send(
            "(" + interface.get_name() + " / " + str(len(pk.data)) + " / " + str(pk.unique_id) + ") " + bytes(pk.data).hex())

    controller_board_manager.green_led_on()

    interface.send_data(pk.data)  # インターフェースにデータを送信
    interface.sending_stopped = True

    if update_time:
        interface.last_sent_packet_unique_id = pk.unique_id
        interface.last_updated_at = time.time()


# json形式のパケットを処理する
def _handle_json_packet(text: str):
    json_dict = json.loads(text)
    pid = int(json_dict['SignalType'])
    uid = int(json_dict['UniqueID'])

    """if pid == NineAxisSensorResultPacket.ID:
        pk = NineAxisSensorResultPacket([])
        pk.unique_id = uid
        pk.acc_x = float(json_dict['AccelX'])
        pk.acc_y = float(json_dict['AccelY'])
        pk.acc_z = float(json_dict['AccelZ'])
        pk.gyro_x = float(json_dict['GyroX'])
        pk.gyro_y = float(json_dict['GyroY'])
        pk.gyro_z = float(json_dict['GyroZ'])
        pk.mag_x = float(json_dict['MagX'])
        pk.mag_y = float(json_dict['MagY'])
        pk.mag_z = float(json_dict['MagZ'])
        pk.encode()
        _process_packet(pk.data)"""

    if pid == SensorDataPacket.ID or pid == NineAxisSensorResultPacket.ID:
        pk = SensorDataPacket([])
        pk.packet_id = SensorDataPacket.ID
        pk.unique_id = uid
        pk.acc_x = float(json_dict['AccelX'])
        pk.acc_y = float(json_dict['AccelY'])
        pk.acc_z = float(json_dict['AccelZ'])
        pk.gyro_x = float(json_dict['GyroX'])
        pk.gyro_y = float(json_dict['GyroY'])
        pk.gyro_z = float(json_dict['GyroZ'])
        pk.dir = float(json_dict['Direction'])
        pk.temp = int(json_dict['Temperature'])
        pk.line_tracer = int(json_dict['LineTracer'])
        pk.encode()
        event_listener.on_sensor_data_resulted(pk)


# 送られてきたパケットを処理する
def _process_packets():
    while core.running:
        if len(received_packets) != 0:
            item = received_packets.popitem()
            split = item[0].split("0d0a")
            interface = item[1]

            for text in split:
                array = bytearray.fromhex(text)
                string = ""

                try:
                    string = array.decode(encoding='utf8')
                except UnicodeDecodeError:
                    pass

                if interface.is_packet_receiving:
                    interface.buffer.extend(array)
                    if len(interface.buffer) == InputPacket.PACKET_LENGTH:
                        _process_packet(interface.buffer)
                        interface.buffer.clear()
                        interface.is_packet_receiving = False
                        continue

                if string.startswith('>#'):
                    _handle_json_packet(string.replace('>#', '').split("\n")[0])
                    continue

                elif string.startswith('>'):
                    logger.debug_i('(' + interface.get_name() + ') ' + string)
                    interface.is_debug_receiving = True
                    continue

                elif len(array) == 0:
                    continue

                # 受信信号（unique_id）
                elif len(array) == 4 and int.from_bytes(array, byteorder='big') == interface.last_sent_packet_unique_id:
                    interface.sending_stopped = False  # パケット送信停止解除
                    interface.last_updated_at = time.time()  # interfaceの最終更新時間を更新
                    interface.packet_resent_count = 0  # 再送回数を0に
                    unique_id = int.from_bytes(array, byteorder='big')
                    # logger.debug("receive: " + str(unique_id))
                    del interface.packet_queue[unique_id]
                    continue

                elif len(array) == InputPacket.PACKET_LENGTH:
                    _process_packet(array)

                elif not interface.is_packet_receiving \
                        and int.from_bytes(array[0:2], byteorder='big') in [10, 20, 30, 40, 50, 60, 70, 80]:
                    interface.is_packet_receiving = True
                    interface.buffer.extend(array)

                # 予期しないパケットのとき
                else:
                    logger.error("(" + interface.get_name() + ") Unexpected Packet Error (" + text + ")")
                    continue


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
                interface.packet_resent_count = 0
                interface.sending_stopped = False
                interface.packet_queue.clear()
                interface.packet_key_queue.clear()
                # exit()

            # _send_packet(interface, interface.packet_queue[interface.last_sent_packet_unique_id])  # 再送する
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
        start_index = 0
        end_index = len(split) - 1

        # フラグメントバッファが空じゃないとき
        if len(interface.fragment_buffer) != 0:
            interface.fragment_buffer += split[0]  # バッファに先頭のデータを追加する
            if len(split) != 1:  # このパケットに他のパケットがあった場合
                received_packets[interface.fragment_buffer] = interface  # 集めたパケットの破片は元通りなので正しいパケットとして登録する
                interface.fragment_buffer = ""  # フラグメントバッファを初期化する
                start_index = 1  # 先頭のデータはフラグメントだったので次のパケットから読む

                if not str(raw_hex).endswith("0d0a"):  # 2個以上のパケットを持っており、かつ最後のデータがあるパケットの一部だった場合
                    interface.fragment_buffer += split[end_index]  # 最後のデータはフラグメントなのでバッファに入れる
                    end_index -= 1

            else:  # このパケットがあるパケットの一部だった場合
                continue  # 次のパケットを読む

        # フラグメントバッファが空のとき
        else:
            if len(split) == 1:  # このパケットがあるパケットの一部だった場合
                interface.fragment_buffer += split[0]  # フラグメントバッファにこのパケットを追加する
                continue

            elif not str(raw_hex).endswith("0d0a"):  # 2個以上のパケットを持っており、かつ最後のデータがあるパケットの一部だった場合
                interface.fragment_buffer += split[end_index]  # 最後のデータはフラグメントなのでバッファに入れる
                end_index -= 1

        # フラグメントになっていない正しい残りのデータを読む
        if start_index <= end_index:
            for i in range(start_index, end_index + 1):
                received_packets[split[i]] = interface


# 受信パケットの処理
def _process_packet(pk_data):
    try:
        packet = InputPacket(pk_data)
        packet.decode()

        # logger.receive("Packet: {}, Unique ID: {}".format(packet.packet_id, packet.unique_id))

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

        elif packet.packet_id == SensorDataPacket.ID:
            pk = SensorDataPacket(packet.data)
            packet.decode()
            event_listener.on_sensor_data_resulted(pk)

    except AssertionError as e:
        logger.error(e)
        return
