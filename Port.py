from eBPDU import *


class Port:

    # "constant" that represent port cost
    COST = 10

    # "constants" that represent port logical states
    class Logical:
        BLOCKED = 0
        ROOT = 1
        DESIGNATED = 2

    # "constants" that represent port forwarding states
    class Forwarding:
        LISTENING = 0
        LEARNING = 1
        FORWARDING = 2

    def __init__(self, port_id, bridge_id):
        # this port's physical details
        self.__sock = None
        self.__port_id = port_id
        self.__bridge_id = bridge_id

        # this port's logical and forwarding status
        self.__logical = Port.Logical.BLOCKED
        self.__forwarding = Port.Forwarding.LISTENING
        self.__forwarding_time = 0

        # this port's BPDU
        self.__bpdu = None

    def spanning_tree_protocol(self):
        self.set_logical_status(Port.Logical.DESIGNATED)
        self.set_forwarding_status(Port.Forwarding.LISTENING)
        self.reset_forwarding_time()
        self.set_bpdu(eBPDU(self.__bridge_id, 0,
                            self.__bridge_id, self.__port_id,
                            0, self.__port_id))

    def set_logical_status(self, logical):
        if logical == Port.Logical.BLOCKED \
            or logical == Port.Logical.DESIGNATED \
                or logical == Port.Logical.ROOT:
            self.__logical = logical
        else:
            raise Exception

    def get_logical_status(self):
        return self.__logical

    def set_forwarding_status(self, forwarding):
        if forwarding == Port.Forwarding.LISTENING \
            or forwarding == Port.Forwarding.LEARNING \
                or forwarding == Port.Forwarding.FORWARDING:
            self.__forwarding = forwarding
        else:
            raise Exception

    def get_forwarding_status(self):
        return self.__forwarding

    def reset_forwarding_time(self):
        self.__forwarding_time = 15

    def decrement_forwarding_time(self):
        self.__forwarding_time -= 1

    def get_forwarding_time(self):
        return self.__forwarding_time

    def is_time_up(self):
        return self.__forwarding_time <= 0

    def time_is_up(self):
        self.__forwarding_time = 0

    def set_bpdu(self, bpdu):
        if isinstance(bpdu, eBPDU):
            self.__bpdu = bpdu
        else:
            raise Exception

    def get_bpdu(self):
        return self.__bpdu

    def set_socket(self, sock):
        self.__sock = sock

    def get_socket(self):
        return self.__sock

    def get_port_id(self):
        return self.__port_id

    def get_bridge_id(self):
        return self.__bridge_id
