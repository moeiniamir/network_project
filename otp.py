import socket
from pickle import loads, dumps
import threading

from sp import *
from utils import *
import re
from firewall import *


class OTP:
    def __init__(self, client_view):
        self.client_view = client_view
        self.chat = None

        self.id = None
        self.rcv_port = None

        self.parent_port = None
        self.parent_id = None
        self.children: list[tuple[int, list[int]]] = []  # list[(port, list[id])]
        self.known_ids = set()

        self.firewall_rules: list[TFirewallRule] = []

    @staticmethod
    def _receive(sock):
        return loads(recv_message(sock))

    @staticmethod
    def _send(data, dest_port, return_ans=False):
        client_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client_sock.connect((HOST, dest_port))
        send_message(client_sock, dumps(data))

        msg = OTP._receive(client_sock) if return_ans else None
        client_sock.close()
        if return_ans:
            return msg

    def _firewall_check(self, packet: Packet):
        for rule in self.firewall_rules[::-1]:
            result = rule.does_pass(packet)
            if result == FirewallResult.Accepted:
                return True
            elif result == FirewallResult.Dropped:
                return False
        return True

    def _known_check(self, packet: Packet):
        if packet.src_id == self.id and packet.dest_id != -1 and packet.dest_id not in self.known_ids:
            self.client_view.unknown_id(packet.dest_id)
            return False
        return True

    def _send_packet(self, packet: Packet):
        if packet.dest_id == self.id:
            return log.error(f'intending to send message to self: {packet}')

        if not (self._firewall_check(packet) and self._known_check(packet)):
            return

        if packet.dest_id == -1:
            from_me_or_children = (packet.src_id == self.id)
            for child_port, subtree in self.children:
                if packet.src_id in subtree:
                    from_me_or_children = True
                else:
                    OTP._send(packet, child_port)
            if self.parent_id != -1 and from_me_or_children:
                OTP._send(packet, self.parent_port)
        else:
            for child_port, subtree in self.children:
                if packet.dest_id in subtree:
                    OTP._send(packet, child_port)
                    break
            else:
                if self.parent_id == -1:
                    not_found_packet = Packet() \
                        .set_type(PacketType.DestinationNotFoundMessage) \
                        .set_src_id(self.id).set_dest_id(packet.src_id) \
                        .set_data(packet.dest_id)

                    self._send_packet(not_found_packet)
                else:
                    OTP._send(packet, self.parent_port)

    def _handle_incoming_packet(self, client_sock: socket.socket):
        packet = self._receive(client_sock)
        if not self._firewall_check(packet):
            return
        if packet.dest_id == -1:  # TODO should we display log for broadcast, too?
            self._send_packet(packet)
            packet.set_dest_id(self.id)
        if packet.dest_id != self.id:
            self.client_view.display_log(packet)
        if packet.dest_id == self.id:
            self.known_ids.add(packet.src_id)

        if packet.type == PacketType.Message:
            if packet.dest_id == self.id:
                self.chat.msg_delivery(packet.src_id, packet.data)
            else:
                self._send_packet(packet)
        elif packet.type == PacketType.RoutingRequest:
            if packet.dest_id == self.id:
                rr_packet = Packet().set_type(PacketType.RoutingResponse) \
                    .set_src_id(self.id).set_dest_id(packet.src_id) \
                    .set_data(f'{self.id}')
                self._send_packet(rr_packet)
            else:
                self._send_packet(packet)
        elif packet.type == PacketType.RoutingResponse:
            from_children = False
            for ch_port, ch_tree in self.children:
                if packet.src_id in ch_tree:
                    from_children = True
                    break

            packet.data = str(self.id) + ('->' if from_children else '<-') + packet.data
            if packet.dest_id == self.id:
                self.client_view.route_delivery(packet.data)
            else:
                self._send_packet(packet)

        elif packet.type == PacketType.ParentAdvertise:
            if packet.dest_id != self.id:
                log.error('parent advertise is not mine')
                return
            new_id = packet.data
            self.known_ids.add(new_id)
            for child_port, subtree in self.children:
                if packet.src_id in subtree:
                    subtree.append(new_id)
                    break
            else:
                log.error('pa: this is not my child')

            if self.parent_id != -1:
                new_packet = packet.set_src_id(self.id).set_dest_id(self.parent_id)
                self._send_packet(new_packet)

        elif packet.type == PacketType.Advertise:
            if packet.dest_id != self.id:
                self._send_packet(packet)
        elif packet.type == PacketType.DestinationNotFoundMessage:
            if packet.dest_id == self.id:
                self.client_view.dest_not_found(packet.data)
            else:
                self._send_packet(packet)
        elif packet.type == PacketType.ConnectionRequest:
            if packet.dest_id == self.id:
                child_port = packet.data
                child_id = packet.src_id
                self.children.append((child_port, [child_id]))
                if self.parent_id != -1:
                    pa_packet = Packet().set_type(PacketType.ParentAdvertise) \
                        .set_src_id(self.id).set_dest_id(self.parent_id) \
                        .set_data(child_id)
                    self._send_packet(pa_packet)
            else:
                log.warning('connection request dest not my id')
        else:
            log.error('packet type not recognized')
        client_sock.close()

    def _listen_incoming_tcp(self):
        server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_sock.bind((HOST, self.rcv_port))
        server_sock.listen()
        while True:
            client_sock, address = server_sock.accept()
            threading.Thread(target=self._handle_incoming_packet, args=(client_sock,)).start()

    def connect_to_network(self, id, rcv_port):
        self.id = id
        self.rcv_port = rcv_port

        msg = f'{self.id} REQUESTS FOR CONNECTING TO NETWORK ON PORT {self.rcv_port}'
        msg = OTP._send(msg, MANAGER_PORT, True)
        m = re.match(r'CONNECT TO (-?\d+) WITH PORT (-?\d+)', msg)
        self.parent_id, self.parent_port = int(m.group(1)), int(m.group(2))
        if self.parent_id != -1:
            self.known_ids.add(self.parent_id)

        conn_req_packet = Packet().set_type(PacketType.ConnectionRequest) \
            .set_src_id(self.id).set_dest_id(self.parent_id) \
            .set_data(self.rcv_port)
        self._send_packet(conn_req_packet)

        threading.Thread(target=self._listen_incoming_tcp).start()

    def send_route_req(self, dest_id):
        rr_packet = Packet().set_type(PacketType.RoutingRequest) \
            .set_src_id(self.id).set_dest_id(dest_id)
        self._send_packet(rr_packet)

    def advertise_to(self, dest_id):
        a_packet = Packet().set_type(PacketType.Advertise) \
            .set_src_id(self.id).set_dest_id(dest_id)
        self._send_packet(a_packet)

    def send_msg(self, data: str, dest_id):
        msg_packet = Packet().set_type(PacketType.Message) \
            .set_src_id(self.id).set_dest_id(dest_id) \
            .set_data(data)
        self._send_packet(msg_packet)

    def add_filter(self, src_id: str, dest_id: str, type: PacketType, action: FirewallAction, dir: FirewallDirection):
        self.firewall_rules.append(TFirewallRule(self.id, src_id, dest_id, type, action, dir))
