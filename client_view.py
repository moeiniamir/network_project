import pickle

from chat import Chat, ChatState
from otp import OTP
from packet import PacketType, Packet
import re
from utils import safe_print
from firewall import FirewallDirection, FirewallAction
from utils import log


class ClientView:
    def __init__(self):
        self.otp: OTP = OTP(self)
        self.chat: Chat = Chat(self)
        self.otp.chat = self.chat
        self.chat.otp = self.otp

    def parse_user_input(self):
        patt0 = r'CONNECT AS (\d+) ON PORT (\d+)'
        patt1 = r'SHOW KNOWN CLIENTS'
        patt2 = r'ROUTE (-?\d+)'
        patt3 = r'ADVERTISE (-?\d+)'
        patt4 = r'SALAM (-?\d+)'
        patt5 = r'START CHAT (\w+): ((?:\d+,?)+)'
        patt6 = r'Y'
        patt7 = r'N'  # Useless
        patt8 = r'EXIT CHAT'
        patt9 = r'FILTER (\w+) (\*|\d+) (\*|\d+) (\d+) (\w+)'
        patt10 = r'FW CHAT (\w+)'

        while True:
            orig_inp = input()
            inp = orig_inp.upper()

            if self.chat.chat_state == ChatState.IN_CHAT:
                m = re.fullmatch(patt8, inp)
                if m:
                    self.chat.exit_chat()
                    continue

                self.chat.send_message(orig_inp)
                continue

            elif self.chat.chat_state == ChatState.INVITATION_PENDING:
                m = re.fullmatch(patt6, inp)
                if m:
                    chat_name = input('Choose a name for yourself: ')
                    self.chat.send_name(chat_name)
                else:  # Anything but 'Y' declines the invitation
                    self.chat.refuse_chat()
                continue
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

                m = re.fullmatch(patt5, inp)
                if m:
                    chat_name = m.group(1)
                    id_list = list(map(int, m.group(2).split(',')))
                    self.chat.start_chat(chat_name, id_list)
                    continue

                m = re.fullmatch(patt9, inp)
                if m:
                    dir = FirewallDirection[m.group(1)]
                    src_id = m.group(2)
                    dest_id = m.group(3)
                    type = PacketType(int(m.group(4)))
                    action = FirewallAction[m.group(5).capitalize()]
                    self.otp.add_filter(src_id, dest_id, type, action, dir)
                    continue

                m = re.fullmatch(patt10, inp)
                if m:
                    action = FirewallAction[m.group(1).capitalize()]
                    self.chat.set_firewall_mode(action)
                    continue

            log.warning(f'invalid input: {inp}')

    # called from OTP
    def display_log(self, packet: Packet):
        if self.chat.chat_state == ChatState.NO_CHAT:
            s = f"{packet.type.name} Packet from {packet.src_id} to {packet.dest_id}"
            safe_print(s)

    def route_delivery(self, route: str):
        if self.chat.chat_state == ChatState.NO_CHAT:
            safe_print(route)

    def dest_not_found(self, dest_id):
        if self.chat.chat_state == ChatState.NO_CHAT:
            s = f"DESTINATION {dest_id} NOT FOUND"
            safe_print(s)

    def unknown_id(self, dest_id):
        if self.chat.chat_state == ChatState.NO_CHAT:
            s = f"Unknown destination {dest_id}"
            safe_print(s)

    # called from Chat
    def display_salam(self, is_ans):
        if is_ans:
            safe_print("Hezaro Sisad Ta Salam")
        else:
            safe_print("Salam Salam Sad Ta Salam")

    def display_message(self, msg: str, chat_name: str):
        s = f"{chat_name}: {msg}"
        safe_print(s)

    def ask_join_name(self, host_chat_name, host_id):
        s = f"{host_chat_name} with id {host_id} has asked you to join a chat. Would you like to join?[Y/N]"
        safe_print(s)

    def so_joined(self, chat_name, id):
        s = f"{chat_name}({id}) was joind to the chat."
        safe_print(s)

    def so_left(self, chat_name, id):
        s = f"{chat_name}({id}) left the chat."
        safe_print(s)

    def blocked_by_firewall(self):
        s = "Chat is disabled. Make sure the firewall allows you to chat."
        safe_print(s)


client = ClientView()
id = 1

try:
    f = open('temp', 'rb')
    id = pickle.load(f)
    f.close()
    client.otp.connect_to_network(id, 3000 + id)
    f = open('temp', 'wb')
    pickle.dump(id + 1, f)
    f.close()
except FileNotFoundError:
    f = open('temp', 'wb')
    client.otp.connect_to_network(1, 3001)
    pickle.dump(2, f)
    f.close()

print(f'Welcome. Try id={id}, port={id + 3000}')
client.parse_user_input()
