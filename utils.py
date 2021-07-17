import logging as log
from threading import Lock
from constants import *

print_lock = Lock()


def safe_print(*args, **kwargs):
    print_lock.acquire()
    print(*args, **kwargs)
    print_lock.release()


log.basicConfig(level=LOGGING_LEVEL)
