from Chat import Chat
from OTP import OTP


class ClientView:
    def __init__(self):
        self.otp: OTP = None
        self.chat: Chat = None

    def parse_user_input(self, inp: str):
        pass

    #### called from OTP
    def display_log(self):
        pass

    def route_delivery(self):
        pass

    #### called from Chat
    def display_message(self):
        pass

    def ask_join_name(self):
        pass
