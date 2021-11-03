def info(text):
    print("[INFO] " + text)


def debug(text):
    print("\033[35m[DEBUG] " + text)


def critical(text):
    print("\033[31m[CRITICAL] \033[0m" + text)


def error(text):
    print("\033[31m[ERROR] \033[0m" + text)


def send(text):
    print("\033[32m[SEND] \033[0m" + text)


def receive(text):
    print("\033[34m[RECEIVE] \033[0m" + text)


def state(text):
    print("\033[33m[STATE] \033[0m" + text)


def debug_i(text):
    print("\033[36m[DEBUG] " + text)
