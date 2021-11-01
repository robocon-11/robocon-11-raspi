import serial
import threading
import time

ser = serial.Serial('/dev/ttyAMA0', 9600)


def _read():
    while ser.in_waiting <= 0:
        print(str(ser.read_all()))


def _write():
    i = 0
    while True:
        ser.write(bytearray(str(i) + '::This is a test message.'))
        i += 1
        time.sleep(1)


if ser is None:
    print("/dev/ttyAMA0 is not found.")
    exit(1)

th = threading.Thread(target=_read)
th.start()

th1 = threading.Thread(target=_write)
th1.start()

