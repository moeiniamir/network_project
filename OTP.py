import socket
from pickle import loads, dumps
import threading
from SP import *
from Constants import *
from Utils import log
import re
from random import randint
from Packet import *

# todo firewall
# todo known ids
# todo handle
# todo interface
class OTP:
    def __init__(self):
        self.server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        self.client_view = None
        self.chat = None

        self.id = None
        self.rcv_port = None
        # self.send_port = None

        self.parent_port = None
        self.parent_id = None
        self.children: list[tuple[int, list[int]]] = []
        self.known_ids = []

    def receive(self, sock):
        try:
            msg = loads(recv_message(sock))
        except:
            log.error('no answer returned')
        return msg

    def send(self, data, dest_port, return_ans=False):
        # self.client_sock.bind((0, self.send_port))
        self.client_sock.connect((HOST, dest_port))
        send_message(self.client_sock, dumps(data))
        if return_ans:
            msg = self.receive(self.client_sock)

        self.client_sock.close()
        if return_ans:
            return msg

    def send_packet(self, packet: Packet):
        for child_port, subtree in self.children:
            if packet.dest_id in subtree:
                self.send(packet, child_port)
                return
        if self.parent_port == -1:
            not_found_packet = Packet() \
                .set_type(PacketType.DestinationNotFoundMessage) \
                .set_src_id(self.id).set_dest_id(packet.src_id) \
                .set_data(f"DESTINATION {packet.dest_id} NOT FOUND")
            self.send_packet(not_found_packet)
        else:
            self.send(packet, self.parent_port)

    def handle_incoming_packet(self, client_sock, address):
        packet = self.receive(client_sock)
        if packet.type == PacketType.Message:
            pass
        elif packet.type == PacketType.RoutingRequest:
            pass
        elif packet.type == PacketType.ParentAdvertise:
            pass
        elif packet.type == PacketType.Advertise:
            pass
        elif packet.type == PacketType.DestinationNotFoundMessage:
            pass
        elif packet.type == PacketType.ConnectionRequest:
            pass
        else:
            log.error('packet type not recognized')

    def listen_incoming_tcp(self):
        while True:
            client_sock, address = self.server_sock.accept()
            threading.Thread(target=self.handle_incoming_packet, args=(client_sock, address)).start()

    def connect_to_network(self, id, rcv_port):
        self.id = id
        self.rcv_port = rcv_port
        # self.send_port = rcv_port + 1

        msg = f"{self.id} REQUESTS FOR CONNECTING TO NETWORK ON PORT {self.rcv_port}"
        msg = self.send(msg, MANAGER_PORT, True)
        m = re.match(r'CONNECT TO (\d+) WITH PORT (\d+)', msg)
        self.parent_id, self.parent_port = int(m.group(1)), int(m.group(2))

        conn_req_packet = Packet().set_type(PacketType.ConnectionRequest) \
            .set_src_id(self.id).set_dest_id(self.parent_id) \
            .set_data(self.rcv_port)
        self.send_packet(conn_req_packet)

        self.server_sock.bind((HOST, self.rcv_port))
        self.server_sock.listen()

        threading.Thread(target=self.listen_incoming_tcp).start()
