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


class TFirewallRule:
    def __init__(self, creator_id, src_id: str, dest_id: str, type: PacketType, action: FirewallAction,
                 dir: FirewallDirection):
        self.creator_id = creator_id
        self.src_id: int = -1 if src_id == '*' else int(src_id)
        self.dest_id: int = -1 if dest_id == '*' else int(dest_id)
        self.type = type
        self.action = action
        self.dir = dir

    def does_pass(self, packet: Packet):
        if self.type != packet.type:
            return FirewallResult.Nothing
        if self.dir == FirewallDirection.OUTPUT:
            if self.creator_id == packet.src_id:
                if self.dest_id == -1 or self.dest_id == packet.dest_id:
                    return FirewallResult(self.action.value)
        elif self.dir == FirewallDirection.INPUT:
            if self.creator_id == packet.dest_id:
                if self.src_id == -1 or self.src_id == packet.src_id:
                    return FirewallResult(self.action.value)
        else:  # Forward
            if (self.src_id == -1 or self.src_id == packet.src_id) \
                    and (self.dest_id == -1 or self.dest_id == packet.dest_id):
                return FirewallResult(self.action.value)
        return FirewallResult.Nothing
