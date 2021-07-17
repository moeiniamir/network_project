import socket
from pickle import loads, dumps
import threading
from sp import *
from constants import *
from utils import log
import re


def handle(client_sock):
    msg = loads(recv_message(client_sock))
    m = re.match(r"(\d+) REQUESTS FOR CONNECTING TO NETWORK ON PORT (\d+)", msg)
    id, port = int(m.group(1)), int(m.group(2))
    parent_indx = (len(nodes_list) - 1) // 2
    nodes_list.append((id, port))
    parent_id, parent_port = nodes_list[parent_indx] if parent_indx >= 0 else (-1, -1)
    msg = f'CONNECT TO {parent_id} WITH PORT {parent_port}'
    send_message(client_sock, dumps(msg))
    client_sock.close()


nodes_list = []
host = HOST
port = MANAGER_PORT

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((host, port))
server.listen()

while True:
    client_sock, address = server.accept()
    thread = threading.Thread(target=handle, args=(client_sock,))
    thread.start()
