#!/usr/bin/python

from eBPDU import *
from Port import *

import argparse
import getpass
import string
import struct
import select
import socket
import sys
import time
import threading


class Bridge:

    def __init__(self, MAC, wires):
        # this bridge's physical details
        self.__table = {}  # key: MAC; value: [time, sock, port]
        self.__MAC = MAC
        self.__ports = {}  # key: socket; value: port
        self.__create_ports(wires)

        # this bridge's BPDU and its true packet
        self.__bpdu = None
        self.__bpdu_packet = None

    def __create_ports(self, wires):
        for w in wires:
            s = socket.socket(socket.AF_UNIX, socket.SOCK_SEQPACKET)
            s.bind('\0%s.bridge-%s-port-%d' \
                   % (getpass.getuser(), self.__MAC, w))
            if s.connect_ex('\0%s.wire.%d' % (getpass.getuser(), w)):
                print 'wire %d broken' % w
                sys.exit(1)
            port = Port(w, self.__MAC)
            port.set_socket(s)
            self.__ports[s] = port

    def turn_on(self):
        thread2 = threading.Thread(target=self.__spanning_tree_protocol)
        thread2.daemon = True
        thread2.start()
        thread3 = threading.Thread(target=self.__send_bpdu_packet)
        thread3.daemon = True
        thread3.start()
        thread4 = threading.Thread(target=self.__port_forwarding_status_timer)
        thread4.daemon = True
        thread4.start()
        thread5 = threading.Thread(target=self.__port_bpdu_age_timer)
        thread5.daemon = True
        thread5.start()
        thread6 = threading.Thread(target=self.__receive_and_react)
        thread6.daemon = True
        thread6.start()
        thread7 = threading.Thread(target=self.__learning_table_timer)
        thread7.daemon = True
        thread7.start()

    def __spanning_tree_protocol(self):
        while True:
            self.__bpdu = eBPDU(self.__MAC, 0, self.__MAC, -1, 0, 0)
            self.__make_bpdu_packet()
            for port in self.__ports.values():
                port.spanning_tree_protocol()
            self.__detect_and_update()

    def __make_bpdu_packet(self):
        R, c, T, a = self.__bpdu.get_values("R c T a")
        ether_dst = struct.pack('6s', ether_aton("01:80:c2:00:00:00"))
        ether_src = struct.pack('6s', ether_aton(self.__MAC))
        length = struct.pack('!H', 0x0026)
        LLC = struct.pack('3B', 0x42, 0x42, 0x03)
        protocol = struct.pack('!H', 0x0000)
        version = struct.pack('B', 0x00)
        types = struct.pack('B', 0x00)
        flags = struct.pack('B', 0x00)
        root_pri = struct.pack('!H', 0x8000)
        root_MAC = struct.pack('6s', ether_aton(R))
        root_cost = struct.pack('!I', c)
        bridge_pri = struct.pack('!H', 0x8000)
        bridge_MAC = struct.pack('6s', ether_aton(T))
        port_id = struct.pack('!H', 0x0000)
        msg_age = struct.pack('!H', a)
        max_age = struct.pack('!H', 0x1400)
        hello = struct.pack('!H', 0x0200)
        forward_delay = struct.pack('!H', 0x0F00)
        null = struct.pack('!Q', 0x0000000000000000)
        bpdu = [ether_dst, ether_src, length, LLC, protocol, version, types,
                flags, root_pri, root_MAC, root_cost, bridge_pri, bridge_MAC,
                port_id, msg_age, max_age, hello, forward_delay, null]
        self.__bpdu_packet = "".join(bpdu)

    def __get_bpdu_packet_with_port_id(self, port):
        return self.__bpdu_packet[:42] + struct.pack(
            '!H', port.get_port_id()) + self.__bpdu_packet[44:]

    def __send_bpdu_packet(self):
        while True:
            ready = select.select([], self.__ports.keys(), [])[1]
            for sock in ready:
                port = self.__ports[sock]
                bpdu = self.__get_bpdu_packet_with_port_id(port)
                sock.send(bpdu)
                R, c, T, a = self.__bpdu.get_values("R c T a")
                print "BPDU %s %d %s %d %d sent. I am %s %s." \
                      % (R, c, T, port.get_port_id(), a,
                         port.get_logical_status(),
                         port.get_forwarding_status())
            time.sleep(2)

    def __detect_and_update(self):
        while True:
            time.sleep(2)

            # declare buffers to store the BPDU comparison results
            best = (self.__bpdu, None)
            better = []
            worse = []
            expired = []

            # compare this bridge's BPDU with each port BPDU
            for port in self.__ports.values():
                port_bpdu = port.get_bpdu()
                not_valid = port_bpdu.is_expired()
                if not_valid:
                    expired.append(port)
                else:
                    rank = port_bpdu.compare_to(self.__bpdu)
                    if rank < 0:
                        better.append((port_bpdu, port))
                        if port_bpdu.compare_to(best[0]) < 0:
                            best = (port_bpdu, port)
                    elif rank > 0:
                        worse.append((port_bpdu, port))
                    else:
                        print "So weird! Two BPDUs are exactly the same. Bye!"
                        sys.exit(1)

            # handle the case when the network topology is broken...
            # change every port with expired BPDU on it to Designated
            root = None
            for port in expired:
                if port.get_logical_status() == Port.Logical.ROOT:
                    root = port
                Bridge.__change_port_status(port, Port.Logical.DESIGNATED)
            # special case happens when root port has expired bpdu.
            # if there are better ports other than the original root port,
            # just pick the port with best non-expired BPDU as new root port.
            # if not, then the spanning tree protocol need to be restarted.
            if root is not None and len(better) == 0:
                break

            # if this bridge is the Root bridge, then do nothing
            if len(better) == 0:
                continue

            # change all ports with better (not best) BPDUs to Blocked status
            for bpdu, port in better:
                if bpdu is not best[0]:
                    Bridge.__change_port_status(port, Port.Logical.BLOCKED)
            
            # change all ports with worse BPDUs to Designated status
            for bpdu, port in worse:
                Bridge.__change_port_status(port, Port.Logical.DESIGNATED)

            # change the port with the best BPDU to Root status
            Bridge.__change_port_status(best[1], Port.Logical.ROOT)

            # set this bridge's BPDU as the best one with self MAC as T
            R, c, p, a, rp = best[0].get_values("R c p a rp")
            c += Port.COST
            T = self.__MAC
            a += eBPDU.ONE_SECOND
            self.__bpdu = eBPDU(R, c, T, p, a, rp)
            self.__make_bpdu_packet()

    @staticmethod
    def __change_port_status(port, logical):
        if logical == Port.Logical.BLOCKED:
            port.set_logical_status(logical)
            port.set_forwarding_status(Port.Forwarding.LISTENING)
            port.time_is_up()
        elif logical == Port.Logical.DESIGNATED \
                or logical == Port.Logical.ROOT:
            previous = port.get_logical_status()
            port.set_logical_status(logical)
            if previous == Port.Logical.BLOCKED:
                port.set_forwarding_status(Port.Forwarding.LISTENING)
                port.reset_forwarding_time()

    def __port_forwarding_status_timer(self):
        while True:
            time.sleep(1)
            for port in self.__ports.values():
                if port.get_logical_status() != Port.Logical.BLOCKED \
                        and port.is_time_up():
                    current = port.get_forwarding_status()
                    if current == Port.Forwarding.LISTENING:
                        port.set_forwarding_status(Port.Forwarding.LEARNING)
                        port.reset_forwarding_time()
                    elif current == Port.Forwarding.LEARNING:
                        port.set_forwarding_status(Port.Forwarding.FORWARDING)
                    else:
                        pass
                elif port.get_logical_status() != Port.Logical.BLOCKED:
                    port.decrement_forwarding_time()

    def __port_bpdu_age_timer(self):
        while True:
            time.sleep(1)
            for port in self.__ports.values():
                bpdu = port.get_bpdu()
                if bpdu.is_expired():
                    pass
                else:
                    bpdu.increment_age()

    def __receive_and_react(self):
        while True:
            ready = select.select(self.__ports.keys(), [], [])[0]
            for sock in ready:
                port = self.__ports[sock]

                # try to receive a packet from the given socket / port
                dgram = sock.recv(1500)
                if not dgram:
                    print 'wire unplugged on port %d.' % port.get_port_id()
                    time.sleep(2)
                    continue
                dst, src = struct.unpack('6s 6s', dgram[0:12])
                dst = ether_ntoa(dst)
                src = ether_ntoa(src)

                # handle the case when the recved packet is BPDU
                if dst == "01:80:c2:00:00:00":
                    R = ether_ntoa(struct.unpack('6s', dgram[24:30])[0])
                    c = int(struct.unpack('!I', dgram[30:34])[0])
                    T = ether_ntoa(struct.unpack('6s', dgram[36:42])[0])
                    p = int(struct.unpack('!H', dgram[42:44])[0])
                    a = int(struct.unpack('!H', dgram[44:46])[0])
                    port.set_bpdu(eBPDU(R, c, T, p, a, port.get_port_id()))
                    print "BPDU %s %d %s %d %d recved. I am %s %s." \
                          % (R, c, T, p, a,
                          port.get_logical_status(),
                          port.get_forwarding_status())
                    continue

                # now start bridging the ethernet packet
                logical = port.get_logical_status()
                forwarding = port.get_forwarding_status()

                # if the port is in blocked status, drop the packet
                if logical == Port.Logical.BLOCKED:
                    print "Port %d is Blocked. Ethernet packet dropped." \
                          % port.get_port_id()

                # if the port is in listening status, also drop the packet
                elif forwarding == Port.Forwarding.LISTENING:
                    print "Port %d is Listening. Ethernet packet dropped." \
                          % port.get_port_id()

                # if the port is in learning status, learn but drop the packet
                elif forwarding == Port.Forwarding.LEARNING:
                    self.__react_learning_table(src, sock, port)
                    print "Port %d is Learning. Source MAC learned only." \
                          % port.get_port_id()

                # if the port is in forwarding status, learn and forward pkt
                elif forwarding == Port.Forwarding.FORWARDING:
                    self.__react_learning_table(src, sock, port)
                    self.__forward_ethernet_packet(dst, port, dgram)
                    print "Port %d is Forwarding. Src learned, Dst forwarded."\
                          % port.get_port_id()

    def __react_learning_table(self, src, sock, port):
        if src not in self.__table:
            self.__table[src] = [15, sock, port]
            print "Source MAC %s with port %d added to table." \
                  % (src, port.get_port_id())
        else:
            self.__table[src] = [15, sock, port]
            print "Source MAC %s with port %d updated on table." \
                  % (src, port.get_port_id())

    def __forward_ethernet_packet(self, dst, port, ether):
        if dst not in self.__table:
            ports = []
            blocked = []
            for s, p in self.__ports.items():
                if p is not port:
                    if p.get_forwarding_status() == Port.Forwarding.FORWARDING:
                        s.send(ether)
                        ports.append(str(p.get_port_id()))
                    else:
                        blocked.append(str(p.get_port_id()))
            if len(ports) != 0:
                print 'Destination MAC %s broadcasted to port %s.' \
                      % (dst, " ".join(ports))
            if len(blocked) != 0:
                print 'Dst MAC %s not broadcasted to blocked port %s.' \
                      % (dst, " ".join(blocked))
        else:
            s, p = self.__table[dst][1:]
            if p is not port:
                if p.get_forwarding_status() == Port.Forwarding.FORWARDING:
                    s.send(ether)
                    print 'Destination MAC %s directed to port %d.' \
                          % (dst, p.get_port_id())
                else:
                    print 'Dst MAC %s not directed to blocked port %d.' \
                          % (dst, p.get_port_id())

    def __learning_table_timer(self):
        while True:
            time.sleep(1)
            expired = []
            for mac, entry in self.__table.items():
                entry[0] -= 1
                if entry[0] <= 0:
                    expired.append(mac)
            for mac in expired:
                del self.__table[mac]


def ether_aton(a):
    a = a.replace('-', ':')
    b = map(lambda x: int(x,16), a.split(':'))
    return reduce(lambda x,y: x+y, map(lambda x: struct.pack('B', x), b))


def ether_ntoa(n):
    return string.join(map(lambda x: "%02x" % x, struct.unpack('6B', n)), ':')


parser = argparse.ArgumentParser(description="A learning bridge simulation")
parser.add_argument('mac', metavar="xx:xx:xx:xx:xx:xx", type=str, nargs=1,
                    help="The MAC address of this bridge")
parser.add_argument('wires', metavar="d", type=int, nargs='+',
                    help="The wires that connect to this bridge's ports")
args = parser.parse_args()


if __name__ == '__main__':
    bridge = Bridge(args.mac[0], args.wires)
    bridge.turn_on()
    while True:
        time.sleep(1)
