from enum import Enum


class PacketType(Enum):
    Message = 0
    RoutingRequest = 10
    RoutingResponse = 11
    ParentAdvertise = 20
    Advertise = 21
    DestinationNotFoundMessage = 31
    ConnectionRequest = 41


class Packet:
    def __init__(self):
        self.type: PacketType = None
        self.src_id: int = None
        self.dest_id: int = None
        self.data = None

    def set_type(self, type: PacketType):
        self.type = type
        return self

    def set_src_id(self, id: int):
        self.src_id = id
        return self

    def set_dest_id(self, id: int):
        self.dest_id = id
        return self

    def set_data(self, data):
        self.data = data
        return self
