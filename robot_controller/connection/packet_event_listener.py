
import core
import robot_manager


class PacketEventListener:
    def __init__(self):
        self.managers = {}  # key: unique_id, value: sensor_manager

    def add_manager(self, unique_id, manager):
        self.managers[unique_id] = manager

    def on_connection_start(self, interface):
        core.instance.on_connection_start(interface.get_name())

    def on_right_stepping_motor_alerted(self, pk):
        pass

    def on_right_stepping_motor_feedback(self, pk):
        self.managers.pop(pk.unique_id).on_receive(pk)

    def on_left_stepping_motor_alerted(self, pk):
        pass

    def on_left_stepping_motor_feedback(self, pk):
        self.managers.pop(pk.unique_id).on_receive(pk)

    def on_distance_sensor_resulted(self, pk):
        self.managers.pop(pk.unique_id).on_receive(pk)

    def on_line_tracer_resulted(self, pk):
        self.managers.pop(pk.unique_id).on_receive(pk)

    def on_nine_axis_sensor_resulted(self, pk):
        self.managers.pop(pk.unique_id).on_receive(pk)

    def on_upper_servo_motor_feedback(self, pk):
        self.managers.pop(pk.unique_id).on_receive(pk)

    def on_bottom_servo_motor_feedback(self, pk):
        self.managers.pop(pk.unique_id).on_receive(pk)

    def on_sensor_data_resulted(self, pk):
        robot_manager.on_sensor_data_resulted(pk)
