import core


class PacketEventListener:
    def __init__(self):
        self.managers = {}  # key: array (packet id), value: sensor_manager

    def on_connection_start(self):
        core.on_connection_start()

    def on_right_stepping_motor_alerted(self, pk):
        pass

    def on_right_stepping_motor_feedback(self, pk):
        self.managers.pop(pk.packet_id).on_receive(pk)

    def on_left_stepping_motor_alerted(self, pk):
        pass

    def on_left_stepping_motor_feedback(self, pk):
        self.managers.pop(pk.packet_id).on_receive(pk)

    def on_distance_sensor_resulted(self, pk):
        self.managers.pop(pk.packet_id).on_receive(pk)

    def on_line_tracer_resulted(self, pk):
        self.managers.pop(pk.packet_id).on_receive(pk)

    def on_nine_axis_sensor_resulted(self, pk):
        self.managers.pop(pk.packet_id).on_receive(pk)

    def on_servo_motor_feedback(self, pk):
        self.managers.pop(pk.packet_id).on_receive(pk)

