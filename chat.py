from otp import OTP
from enum import Enum
import re
from utils import log
from random import randint
from constants import *
from firewall import FirewallAction


class ChatState(Enum):
    IN_CHAT = 0
    NO_CHAT = 1
    INVITATION_PENDING = 2


class Chat:
    def __init__(self, client_view):
        self.client_view = client_view
        self.otp: OTP = None
        self.chat_state: ChatState = ChatState.NO_CHAT
        self.invited: list[int] = []
        self.id_name: dict[int: str] = {}
        self.chat_name = None
        self.chat_id: int = None
        self.firewall_mode = FirewallAction.Accept

    # called from OTP
    def msg_delivery(self, src_id: int, msg: str):
        patt0 = r"Hezaro Sisad Ta Salam"
        patt1 = r"CHAT (\d+):\nREQUESTS FOR STARTING CHAT WITH (\w+): ((?:\d+,?)+)"
        patt2 = r"CHAT (\d+):\n(\d+) :(\w+)"
        patt3 = r"CHAT (\d+):\nEXIT CHAT (\d+)"
        patt4 = r"CHAT (\d+):\n(.*)"
        patt5 = r"Salam Salam Sad Ta Salam"

        m = re.fullmatch(patt0, msg)
        if m:
            if self.chat_state == ChatState.NO_CHAT:
                self.client_view.display_salam(True)
            return

        m = re.fullmatch(patt1, msg)
        if m:
            if self.chat_state == ChatState.NO_CHAT and self.firewall_mode == FirewallAction.Accept:
                self.chat_state = ChatState.INVITATION_PENDING
                self.chat_id = int(m.group(1))
                host_chat_name = m.group(2)
                self.invited = list(map(int, m.group(3).split(',')))
                self.invited.remove(self.otp.id)
                self.otp.known_ids.update(self.invited)
                host_id = self.invited[0]
                self.id_name[host_id] = host_chat_name
                self.client_view.ask_join_name(host_chat_name, host_id)
            return

        m = re.fullmatch(patt2, msg)
        if m:
            chat_id = int(m.group(1))
            id = int(m.group(2))
            chat_name = m.group(3)
            self.id_name[id] = chat_name
            if chat_id == self.chat_id and self.chat_state == ChatState.IN_CHAT:
                self.client_view.so_joined(chat_name, id)
            return

        m = re.fullmatch(patt3, msg)
        if m:
            if self.chat_state == ChatState.IN_CHAT:
                chat_id = int(m.group(1))
                if self.chat_id == chat_id:
                    id = int(m.group(2))
                    chat_name = self.id_name.pop(id)
                    self.client_view.so_left(chat_name, id)
            return

        m = re.fullmatch(patt4, msg)
        if m:
            if self.chat_state == ChatState.IN_CHAT:
                chat_id = int(m.group(1))
                if self.chat_id == chat_id:
                    msg = m.group(2)
                    chat_name = self.id_name[src_id]
                    self.client_view.display_message(msg, chat_name)
            return

        m = re.fullmatch(patt5, msg)
        if m:
            msg = f'Hezaro Sisad Ta Salam'
            self.otp.send_msg(msg, src_id)
            if self.chat_state == ChatState.NO_CHAT:
                self.client_view.display_salam(False)
            return

        log.warning(f'unknown message packet arrived: {msg}')

    # called from ClientView
    def send_salam(self, dest_id):
        msg = 'Salam Salam Sad Ta Salam'
        self.otp.send_msg(msg, dest_id)

    def start_chat(self, chat_name, others: list[int]):
        if self.firewall_mode == FirewallAction.Drop:
            self.client_view.blocked_by_firewall()
            return

        for id in others:
            if id not in self.otp.known_ids:
                log.warning(f'{id} is unknown. omitted from chat.')
        others = [id for id in others if id in self.otp.known_ids]

        self.chat_state = ChatState.IN_CHAT
        self.invited = others
        self.chat_name = chat_name
        self.chat_id = randint(CHAT_ID_MIN, CHAT_ID_MAX)

        id_list_str = list(map(str, [self.otp.id] + others))
        msg = f"CHAT {self.chat_id}:\nREQUESTS FOR STARTING CHAT WITH {chat_name}: " + ','.join(id_list_str)
        for id in others:
            self.otp.send_msg(msg, id)

    def send_name(self, chat_name):
        self.chat_state = ChatState.IN_CHAT
        self.chat_name = chat_name
        msg = f"CHAT {self.chat_id}:\n{self.otp.id} :{chat_name}"
        for id in self.invited:
            self.otp.send_msg(msg, id)

    def refuse_chat(self):
        self.invited.clear()
        self.chat_id = None
        self.chat_state = ChatState.NO_CHAT

    def exit_chat(self):
        msg = f'CHAT {self.chat_id}:\nEXIT CHAT {self.otp.id}'
        for id in self.invited:
            self.otp.send_msg(msg, id)

        self.invited.clear()
        self.chat_name = None
        self.chat_id = None
        self.chat_state = ChatState.NO_CHAT

    def send_message(self, msg: str):
        msg = f'CHAT {self.chat_id}:\n{msg}'
        for id in self.invited:
            self.otp.send_msg(msg, id)

    def set_firewall_mode(self, action: FirewallAction):
        self.firewall_mode = action
