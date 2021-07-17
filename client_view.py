from chat import Chat, ChatState
from otp import OTP
from packet import PacketType, Packet
import re
from utils import safe_print


class ClientView:
    def __init__(self):
        self.otp: OTP = OTP(self)
        self.chat: Chat = Chat(self)
        self.otp.chat = self.chat
        self.chat.otp = self.otp

    def parse_user_input(self):
        patt0 = r"CONNECT AS (\d+) ON PORT (\d+)"
        patt1 = r"SHOW KNOWN CLIENTS"
        patt2 = r"ROUTE (-?\d+)"
        patt3 = r"Advertise (-?\d+)"
        patt4 = r"Salam (-?\d+)"
        patt5 = r"START CHAT (\w+): ((?:\d+,?)+)"
        patt6 = r"Y"
        patt7 = r"N"
        patt8 = r"(\w+)"
        patt9 = r"EXIT CHAT"
        patt10 = r"FILTER (\w+) (\d+) (\d+) (\d+) (\w+)"
        patt11 = r"FW CHAT (\w+)"


        while True:
            inp = input()

            if self.chat.chat_state == ChatState.IN_CHAT:
                m = re.fullmatch(patt9, inp)
                if m:
                    self.chat.exit_chat()
                    continue

                self.chat.send_message(inp)

            elif self.chat.chat_state == ChatState.INVITATION_PENDING:
                pass
            else:
                m = re.fullmatch(patt0, inp)
                if m:
                    id = int(m.group(1))
                    port = int(m.group(2))
                    self.otp.connect_to_network(id, port)
                    continue

                m = re.fullmatch(patt1, inp)
                if m:
                    safe_print(self.otp.known_ids)
                    continue

                m = re.fullmatch(patt2, inp)
                if m:
                    dest_id = int(m.group(1))
                    self.otp.send_route_req(dest_id)
                    continue

                m = re.fullmatch(patt3, inp)
                if m:
                    dest_id = int(m.group(1))
                    self.otp.advertise_to(dest_id)
                    continue

                m = re.fullmatch(patt4, inp)
                if m:
                    dest_id = int(m.group(1))
                    self.chat.send_salam(dest_id)
                    continue


    #### called from OTP
    def display_log(self, packet: Packet):
        s = f"{packet.type.name} Packet from {packet.src_id} to {packet.dest_id}"
        safe_print(s)

    def route_delivery(self, route: str):
        safe_print(route)

    def dest_not_found(self, dest_id):
        s = f"DESTINATION {dest_id} NOT FOUND"
        safe_print(s)

    #### called from Chat
    def display_salam(self):
        pass

    def display_message(self, msg: str):
        pass

    def ask_join_name(self, host_chat_name, host_id):
        pass

    def so_joined(self, chat_name, id):
        pass

    def so_left(self, chat_name, id):
        pass

    def blocked_by_firewall(self):
        pass


client = ClientView()
client.parse_user_input()
