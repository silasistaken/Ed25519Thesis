# https://datatracker.ietf.org/doc/html/rfc8032#appendix-A
import os
import hashlib
from micropython import const

_CONST_P = const(57896044618658097711785492504343953926634992332820282019728792003956564819949)
_CONST_D = const(37095705934669439343138083508754565189542113879843219016388785533085940283555)


# A point on Edwards25519.
class Edwards25519Point:
    # FIELD OPS
    # Compute candidate square root of x modulo p, with p = 5 (mod 8) [special case]
    def sqrt8k5(self, x2):
        # candidate= x2^((p+3)//8) %p
        candidate = pow(x2, 7237005577332262213973186563042994240829374041602535252466099000494570602494, _CONST_P)
        # If the square root exists, it is either candidate or candidate*2^(p-1)/4.
        if (candidate * candidate) % _CONST_P == x2 % _CONST_P:  # candidate^2 == x2 (mod  p) -> candidate is square root
            return candidate
        else:  # candidate^2 == - x2 -> 2^((p-1)/4) * x is square root (or x2 is not a square % p, deferred to caller)
            z = pow(2, 14474011154664524427946373126085988481658748083205070504932198000989141204987, _CONST_P)
            return (candidate * z) % _CONST_P

    # Field inverse (inverse of 0 is 0).
    def inv(self, x):
        return pow(x, _CONST_P - 2, _CONST_P)

    def sqrt(self, x):
        # candidate= x2^((p+3)//8) %p
        candidate = pow(x, 7237005577332262213973186563042994240829374041602535252466099000494570602494, _CONST_P)
        # If the square root exists, it is either candidate or candidate*2^(p-1)/4.
        if (candidate * candidate) % _CONST_P == x % _CONST_P:  # candidate^2 == x2 (mod  p) -> candidate is square root
            y = candidate
        else:  # candidate^2 == - x2 -> 2^((p-1)/4) * x is square root (or x2 is not a square % p, deferred to caller)
            z = pow(2, 14474011154664524427946373126085988481658748083205070504932198000989141204987, _CONST_P)
            y = (candidate * z) % _CONST_P

        # Check square root candidate valid.
        if (y * y) % _CONST_P == x:
            return y
        else:
            return None

    def iszero(self, x):
        return x == 0

    def sign(self, x):
        return x & 1

    # Serialize number to 32 bytes.
    def tobytes(self, x):
        return x.to_bytes(32, "little")

    # turns bits into an integer
    # returns none if the extracted number is >= p
    def frombytes(self, x):
        # rv = int.from_bytes(x, "little") % (2 ** (255))
        rv = int.from_bytes(x, "little") % 57896044618658097711785492504343953926634992332820282019728792003956564819968
        return rv if rv < _CONST_P else None

    # END FIELD OPS

    def initpoint(self, x, y):
        self.x = x % _CONST_P
        self.y = y % _CONST_P
        self.z = 1

    # multiply a point with a scalar
    def __mul__(self, x: int):
        # adding a point p to the neutral element results in p
        r = self.zero_elem()
        s = self
        while x > 0:
            # x uneven, add s one extra time
            if (x % 2) > 0:
                r = r + s
            # double point, adding it to itself
            # i.e. s = [2]s
            # doing this multiple times gives: [2]*[2]*...*[2]s = [2^n]s
            s = s.double()
            x = x // 2
        return r

    # Check that two points are equal.
    def __eq__(self, y):
        # Need to check x1/z1 == x2/z2 and similarly for y, so cross
        # multiply to eliminate divisions.
        xn1 = (self.x * y.z) % _CONST_P
        xn2 = (y.x * self.z) % _CONST_P
        yn1 = (self.y * y.z) % _CONST_P
        yn2 = (y.y * self.z) % _CONST_P
        return xn1 == xn2 and yn1 == yn2

    # Check if two points are not equal.
    def __ne__(self, y):
        return not (self == y)

    def __init__(self, x, y):
        # Check the point is actually on the curve.
        if (y * y - x * x) % _CONST_P != (1 + _CONST_D * x * x * y * y) % _CONST_P:
            raise ValueError("Invalid point")
        self.initpoint(x, y)
        self.t = (x * y) % _CONST_P

    # Decode a point representation.
    def decode(self, s):
        # Check that point encoding is the correct length.
        if len(s) != 32:
            return None
        # Extract signbit (most significant bit)
        xs = s[31] >> (255 & 7)
        # Decode y.  If this fails, fail.
        y = self.frombytes(s)
        if y is None:
            return None
        # Try to recover x.  If it does not exist, or if zero and xs
        # are wrong, fail.
        x = self.sqrt(self.solve_x2(y))
        if x is None or (self.iszero(x) and xs != self.sign(x)):
            return None
        x = x % _CONST_P
        # If sign of x isn't correct, flip it.
        if self.sign(x) != xs:
            x = (_CONST_P - x) % _CONST_P
        return Edwards25519Point(x, y)

    # Encode a point as a 32 byte string
    def encode(self):
        xp, yp = (self.x * self.inv(self.z)) % _CONST_P, (self.y * self.inv(self.z)) % _CONST_P
        # Encode y.
        s = bytearray(self.tobytes(yp))
        # Add sign bit of x to encoding.
        if self.sign(xp) != 0:
            s[31] |= 1 << 7
        return s

    # Construct a neutral point on this curve.
    def zero_elem(self):
        return Edwards25519Point(0, 1)

    # Solve for x^2.
    def solve_x2(self, y):
        return (((y * y - 1) % _CONST_P) * self.inv((_CONST_D * y * y + 1) % _CONST_P)) % _CONST_P

    # Point addition.
    def __add__(self, y):
        tmp = self.zero_elem()
        zcp = (self.z * y.z) % _CONST_P
        A = (((_CONST_P + self.y - self.x) % _CONST_P) * ((_CONST_P + y.y - y.x) % _CONST_P)) % _CONST_P
        B = (((self.y + self.x) % _CONST_P) * ((y.y + y.x) % _CONST_P)) % _CONST_P
        C = ((((_CONST_D + _CONST_D) % _CONST_P) * self.t * y.t) % _CONST_P) % _CONST_P
        D = (zcp + zcp) % _CONST_P
        E, H = (_CONST_P + B - A) % _CONST_P, (B + A) % _CONST_P
        F, G = (_CONST_P + D - C) % _CONST_P, (D + C) % _CONST_P
        tmp.x, tmp.y, tmp.z, tmp.t = (E * F) % _CONST_P, (G * H) % _CONST_P, (F * G) % _CONST_P, (E * H) % _CONST_P
        return tmp

    # Point doubling.
    def double(self):
        tmp = self.zero_elem()
        A = (self.x * self.x) % _CONST_P
        B = (self.y * self.y) % _CONST_P
        Ch = (self.z * self.z) % _CONST_P
        C = (Ch + Ch) % _CONST_P
        H = (A + B) % _CONST_P
        xys = (self.x + self.y) % _CONST_P
        E = (_CONST_P + H - ((xys * xys) % _CONST_P)) % _CONST_P
        G = (_CONST_P + A - B) % _CONST_P
        F = (C + G) % _CONST_P
        tmp.x, tmp.y, tmp.z, tmp.t = (E * F) % _CONST_P, (G * H) % _CONST_P, (F * G) % _CONST_P, (E * H) % _CONST_P
        return tmp


B = Edwards25519Point(15112221349535400772501151409588531511454012693041857206046113283949847762202,
                      46316835694926478169428394003475163141307993866256225615783033603165251855960)  # base point



# prune buffer/private scalar
def prune(a):
    _a = bytearray(a)
    # clears the lowest 3 bits
    _a[0] &= ~(1 << 0)
    _a[0] &= ~(1 << 1)
    _a[0] &= ~(1 << 2)
    # set the 2nd highest bit
    _a[31] |= 1 << 6
    # clear the highest bit
    _a[31] &= ~(1 << (7 % 8))
    return _a


# key generation
def keygen(priv):
    # no private key, generate a random one.
    if priv is None:
        priv = os.urandom(32)

    # derive public key
    k = hashlib.sha512(priv).digest()
    a = int.from_bytes((prune(k[:32])), "little")
    return priv, (B * a).encode()




def sign(priv, pub, msg):
    k = hashlib.sha512(priv).digest()
    s = int.from_bytes((prune(k[:32])), "little")
    upper = k[32:]
    # Calculate r and R (R only used in encoded form).
    r = int.from_bytes(hashlib.sha512(
        (upper + msg)).digest(),
                       "little") % 7237005577332262213973186563042994240857116359379907606001950938285454250989
    R = (B * r).encode()
    k = int.from_bytes(hashlib.sha512((R + pub + msg)).digest(),
                       "little") % 7237005577332262213973186563042994240857116359379907606001950938285454250989
    S = ((r + k * s) % 7237005577332262213973186563042994240857116359379907606001950938285454250989).to_bytes(32,
    # concatenation of R and S
    return R + S


def verify(pubkey, msg, sig):
    if len(sig) != 64:
        return False
    if len(pubkey) != 32:
        return False
    # Split signature into R and S
    lower, upper = sig[:32], sig[32:]
    R, S = B.decode(lower), int.from_bytes(upper, "little")
    # Parse public key
    A = B.decode(pubkey)
    # Check parse results
    if (R is None) or (
            A is None) or S >= 7237005577332262213973186563042994240857116359379907606001950938285454250989:  # S>=L
        return False
    # Calculate k % L
    k = int.from_bytes((hashlib.sha512((
            lower + pubkey + msg)).digest()),
                       "little") % 7237005577332262213973186563042994240857116359379907606001950938285454250989
    # Calculate left and right sides of group equation
    rhs = R + A * k
    lhs = B * S
    # group equation [8][S]B == [8]R + [8][k]A, 2^3=8
    for i in range(0, 3):
        lhs = lhs.double()
        rhs = rhs.double()
    # Check eq. holds?
    return lhs == rhs


