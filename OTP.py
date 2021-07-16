import socket
from pickle import loads, dumps
import threading

from Chat import Chat
from ClientView import ClientView
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

        self.client_view: ClientView = None
        self.chat: Chat = None

        self.id = None
        self.rcv_port = None
        # self.send_port = None

        self.parent_port = None
        self.parent_id = None
        self.children: list[tuple[int, list[int]]] = []
        self.known_ids = set()

    def _receive(self, sock):
        msg = loads(recv_message(sock))
        return msg

    def _send(self, data, dest_port, return_ans=False):
        # self.client_sock.bind((0, self.send_port))
        self.client_sock.connect((HOST, dest_port))
        send_message(self.client_sock, dumps(data))
        if return_ans:
            msg = self._receive(self.client_sock)

        self.client_sock.close()
        if return_ans:
            return msg

    def _send_packet(self, packet: Packet):
        for child_port, subtree in self.children:
            if packet.dest_id in subtree or packet.dest_id == -1:
                self._send(packet, child_port)
        else:
            if self.parent_port == -1:
                not_found_packet = Packet() \
                    .set_type(PacketType.DestinationNotFoundMessage) \
                    .set_src_id(self.id).set_dest_id(packet.src_id) \
                    .set_data(f"DESTINATION {packet.dest_id} NOT FOUND")
                self._send_packet(not_found_packet)
            else:
                self._send(packet, self.parent_port)

    def _handle_incoming_packet(self, client_sock, address):
        packet = self._receive(client_sock)
        self.known_ids.add(packet.src_id)

        if packet.type == PacketType.Message:
            self.chat.msg_delivery(packet.src_id, packet.data)
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

    def _listen_incoming_tcp(self):
        while True:
            client_sock, address = self.server_sock.accept()
            threading.Thread(target=self._handle_incoming_packet, args=(client_sock, address)).start()

    def connect_to_network(self, id, rcv_port):
        self.id = id
        self.rcv_port = rcv_port
        # self.send_port = rcv_port + 1

        msg = f"{self.id} REQUESTS FOR CONNECTING TO NETWORK ON PORT {self.rcv_port}"
        msg = self._send(msg, MANAGER_PORT, True)
        m = re.match(r'CONNECT TO (\d+) WITH PORT (\d+)', msg)
        self.parent_id, self.parent_port = int(m.group(1)), int(m.group(2))

        conn_req_packet = Packet().set_type(PacketType.ConnectionRequest) \
            .set_src_id(self.id).set_dest_id(self.parent_id) \
            .set_data(self.rcv_port)
        self._send_packet(conn_req_packet)

        self.server_sock.bind((HOST, self.rcv_port))
        self.server_sock.listen()

        threading.Thread(target=self._listen_incoming_tcp).start()

    def send_route_req(self, dest_id):
        pass

    def advertise_to(self, dest_id):
        pass

    def send_msg(self, data: str, dest_id):
        pass
