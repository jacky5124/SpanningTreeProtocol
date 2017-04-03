#!/usr/bin/env python

import sys
import binascii
import collections


class Ethernet:
    def __init__(self):
        self.fields = collections.OrderedDict()
        self.fields["ether_dst"] = "000000000000"
        self.fields["ether_src"] = "000000000000"
        self.fields["length"] = "0026"
        self.fields["LLC"] = "424203"
        self.bpdu = None

    def has_field(self, field):
        return self.fields.get(field)

    def update(self, field, value):
        self.fields[field] = value

    def display(self):
        out = []
        out.append("ether_src " + append_columns(self.fields["ether_src"]) + "\n")
        out.append("ether_dst " + append_columns(self.fields["ether_dst"]) + "\n")
        return "".join(out)

    def get_values(self):
        out = []
        for key, value in self.fields.items():
            out.append(value)
        return "".join(out)

    def set_spanning_tree(self, bpdu):
        self.bpdu = bpdu

    def get_spanning_tree(self):
        return self.bpdu


class BPDU:
    def __init__(self):
        self.fields = collections.OrderedDict()
        self.fields["protocol"] = "0000"
        self.fields["version"] = "00"
        self.fields["type"] = "00"
        self.fields["flags"] = "00"
        self.fields["stp_root_pri"] = "0000"
        self.fields["stp_root_mac"] = "000000000000"
        self.fields["stp_root_cost"] = "00000000"
        self.fields["stp_bridge_pri"] = "0000"
        self.fields["stp_bridge_mac"] = "000000000000"
        self.fields["stp_port_id"] = "0000"
        self.fields["stp_msg_age"] = "0000"
        self.fields["max_age"] = "1400"
        self.fields["hello_time"] = "0200"
        self.fields["forward_delay"] = "0F00"

    def has_field(self, field):
        return self.fields.get(field)

    def update(self, field, value):
        self.fields[field] = value

    def display(self):
        out = []
        out.append("type " + str(int(self.fields["type"], 16)) + "\n")
        out.append("flags " + str(int(self.fields["flags"], 16)) + "\n")
        out.append("stp_root_pri " + str(int(self.fields["stp_root_pri"], 16)) + "\n")
        out.append("stp_root_cost " + str(int(self.fields["stp_root_cost"], 16)) + "\n")
        out.append("stp_bridge_pri " + str(int(self.fields["stp_bridge_pri"], 16)) + "\n")
        out.append("stp_port_id " + str(int(self.fields["stp_port_id"], 16)) + "\n")
        out.append("stp_msg_age " + str(int(self.fields["stp_msg_age"], 16)) + "\n")
        out.append("stp_root_mac " + append_columns(self.fields["stp_root_mac"]) + "\n")
        out.append("stp_bridge_mac " + append_columns(self.fields["stp_bridge_mac"]) + "\n")
        return "".join(out)

    def get_values(self):
        out = []
        for value in self.fields.values():
            out.append(value)
        return "".join(out)


def decode(ethernet, bpdu):

    # read binary from standard input
    temp = sys.stdin.read()

    # convert the read binary into hex numbers, two digit per byte
    temp = binascii.hexlify(temp)

    # checks whether the packet format is correct
    if temp[24:28] != "0026" or temp[28:34] != "424203"\
        or temp[34:38] != "0000" or temp[38:40] != "00"\
            or temp[40:42] != "00" or temp[42:44] != "00":
        print("ERROR")
        sys.exit(1)

    # begin updating the packet values
    ethernet.update("ether_dst", temp[0:12])
    ethernet.update("ether_src", temp[12:24])
    ethernet.update("length", temp[24:28])
    ethernet.update("LLC", temp[28:34])
    bpdu.update("protocol", temp[34:38])
    bpdu.update("version", temp[38:40])
    bpdu.update("type", temp[40:42])
    bpdu.update("flags", temp[42:44])
    bpdu.update("stp_root_pri", temp[44:48])
    bpdu.update("stp_root_mac", temp[48:60])
    bpdu.update("stp_root_cost", temp[60:68])
    bpdu.update("stp_bridge_pri", temp[68:72])
    bpdu.update("stp_bridge_mac", temp[72:84])
    bpdu.update("stp_port_id", temp[84:88])
    bpdu.update("stp_msg_age", temp[88:92])
    bpdu.update("max_age", temp[92:96])
    bpdu.update("hello_time", temp[96:100])
    bpdu.update("forward_delay", temp[100:104])
    # end updating the packet values

    # write the decoded result into standard output
    sys.stdout.write(ethernet.display() + bpdu.display())


def encode(ethernet, bpdu):

    # read text from standard input line by line
    data = sys.stdin.readline()

    # if there is a line, process that line
    while data:

        # a line consists of a field name and its value, so split it
        args = data.split()

        # process data that belongs to an ethernet packet
        if ethernet.has_field(args[0]):
            if args[0] == "ether_dst" or args[0] == "ether_src":
                temp = args[1].replace(":", "")
            elif args[0] == "length":
                temp = dec_to_hex(args[1], 4)
            else:
                temp = dec_to_hex(args[1], 6)
            ethernet.update(args[0], temp)

        # process data that belongs to an spanning tree packet
        elif bpdu.has_field(args[0]):
            if args[0] == "stp_root_mac" or args[0] == "stp_bridge_mac":
                temp = args[1].replace(":", "")
            elif args[0] == "version" or args[0] == "type" \
                    or args[0] == "flags":
                temp = dec_to_hex(args[1], 2)
            elif args[0] == "stp_root_cost":
                temp = dec_to_hex(args[1], 8)
            else:
                temp = dec_to_hex(args[1], 4)
            bpdu.update(args[0], temp)

        # if the line is malformed, then there is a problem
        else:
            print("ERROR")
            sys.exit(1)

        # after processing a line, read the next line
        data = sys.stdin.readline()

    # after processing, write the result into standard output as binary
    sys.stdout.write(binascii.unhexlify(
        ethernet.get_values() + bpdu.get_values() + "0000000000000000"))


def append_columns(hexstr):
    return ":".join([hexstr[i:i+2] for i in range(0, len(hexstr), 2)])


def strip_columns(hexstr):
    return hexstr.replace(":", "")


def dec_to_hex(value, length):
    temp = hex(int(value))[2:]
    out = []
    for i in range(length - len(temp)):
        out.append('0')
    out.append(temp)
    return "".join(out)


if __name__ == "__main__":
    op = sys.argv[1]
    ethernet_packet = Ethernet()
    spanning_tree_packet = BPDU()
    if op == "decode":
        decode(ethernet_packet, spanning_tree_packet)
    elif op == "encode":
        encode(ethernet_packet, spanning_tree_packet)
    else:
        print("invalid operation")
