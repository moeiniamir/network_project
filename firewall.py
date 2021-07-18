from enum import Enum
from packet import Packet, PacketType


class FirewallDirection(Enum):
    INPUT = 0
    OUTPUT = 1
    FORWARD = 2


class FirewallAction(Enum):
    Accept = 0
    Drop = 1

class FirewallResult(Enum):
    Accepted = 0
    Dropped = 1
    Nothing = 2

# todo does_pass
class TFirewallRule:
    def __init__(self, src_id: str, dest_id: str, type: PacketType, action: FirewallAction, dir: FirewallDirection):
        self.src_id: int = -1 if src_id == '*' else int(src_id)
        self.dest_id: int = -1 if dest_id == '*' else int(src_id)
        self.type = type
        self.action = action
        self.dir = dir

    def does_pass(self, packet: Packet):
        return FirewallResult.Accepted