import serial

MOTOR_LEFT = 0   # 左モータ
MOTOR_RIGHT = 1  # 右モータ

# ls /devでシリアル通信先を確認!!
ser = serial.Serial('/dev/ttyUSB0', 9600)
if ser is None:
    print('Error')

# モータの駆動
# motor_num: モータ番号, degree: 回転角（度数法）
def rotate_motor(motor_num, degree):
    print(motor_num)
