from logging import getLogger
from threading import Lock

print_lock = Lock()


def safe_print(*args, **kwargs):
    print_lock.acquire()
    print(*args, **kwargs)
    print_lock.release()


log = getLogger('global_logger')
