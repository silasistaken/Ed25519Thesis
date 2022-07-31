import time


# this file runs when the ESP32 boots

# wrapped in functions to avoid endless loops of memory errors
def tf():
    import test_vectors
    test_vectors.run(11)


def run():
    import myhash
    import hashlib

    msg_short = b'short message'
    msg_long = b'short message' * 1024

    t1 = time.ticks_ms()
    # do stuff here
    h1 = myhash.sha512(msg_short).digest()
    t2 = time.ticks_ms()
    # do stuff here
    h2 = hashlib.sha512(msg_short).digest()
    t3 = time.ticks_ms()
    print(f"myhash short msg took   {time.ticks_diff(t2, t1)} ms")
    print(f"hashlib short msg took  {time.ticks_diff(t3, t2)} ms")
    print(f"h1 == h2 ? {h1 == h2}")

    t1 = time.ticks_ms()
    # do stuff here
    h1 = myhash.sha512(msg_long).digest()

    t2 = time.ticks_ms()
    # do stuff here
    h2 = hashlib.sha512(msg_long).digest()

    t3 = time.ticks_ms()
    print(f"myhash long msg took   {time.ticks_diff(t2, t1)} ms")
    print(f"hashlib long msg took  {time.ticks_diff(t3, t2)} ms")
    print(f"h1 == h2 ? {h1 == h2}")
