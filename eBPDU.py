class eBPDU:

    ONE_SECOND = 256
    MAX_AGE = 5120

    def __init__(self, R, c, T, p, a, rp=None):
        self.__R = mac_to_int(R)
        self.__c = c
        self.__T = mac_to_int(T)
        self.__p = p
        self.__a = a
        self.__rp = rp

    def update_values(self, R=None, c=None, T=None, p=None, a=None, rp=None):
        if R is not None:
            self.__R = mac_to_int(R)
        if c is not None:
            self.__c = c
        if T is not None:
            self.__T = mac_to_int(T)
        if p is not None:
            self.__p = p
        if a is not None:
            self.__a = a
        if rp is not None:
            self.__rp = rp

    def get_values(self, args=None):
        if args is None:
            return int_to_mac(self.__R), self.__c, \
                   int_to_mac(self.__T), self.__p, \
                   self.__a, self.__rp
        out = []
        options = args.strip().split()
        if "R" in options:
            out.append(int_to_mac(self.__R))
        if "c" in options:
            out.append(self.__c)
        if "T" in options:
            out.append(int_to_mac(self.__T))
        if "p" in options:
            out.append(self.__p)
        if "a" in options:
            out.append(self.__a)
        if "rp" in options:
            out.append(self.__rp)
        return out

    def reset_age(self):
        self.__a = 0

    def increment_age(self):
        self.__a += eBPDU.ONE_SECOND

    def get_age(self):
        return self.__a

    def is_expired(self):
        return self.__a >= eBPDU.MAX_AGE

    def compare_to(self, bpdu):
        return eBPDU.compare(self, bpdu)

    @staticmethod
    def compare(left, right):
        if left.__R < right.__R:
            return -1
        if left.__R > right.__R:
            return 1
        if left.__c < right.__c:
            return -1
        if left.__c > right.__c:
            return 1
        if left.__T < right.__T:
            return -1
        if left.__T > right.__T:
            return 1
        if left.__p < right.__p:
            return -1
        if left.__p > right.__p:
            return 1
        if left.__rp is not None \
                and right.__rp is not None:
            if left.__rp < right.__rp:
                return -1
            if left.__rp > right.__rp:
                return 1
        return 0


def mac_to_int(mac):
    return int(mac.replace(":", ""), 16)


def int_to_mac(integer):
    temp = hex(integer)[2:]
    out = []
    for i in range(12 - len(temp)):
        out.append('0')
    out.append(temp)
    out = "".join(out)
    out = [out[i:i+2] for i in xrange(0, len(out), 2)]
    return ":".join(out)
