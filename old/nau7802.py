#!/usr/bin/env python

import smbus
import sys
import time

ADDR = 0x2a
OFFSETS = { 1: -0.077, 2: -0.012 }

'''
http://www.raspberry-projects.com/pi/programming-in-python/i2c-programming-in-python/using-the-i2c-interface-2
'''

def get_reading(bus):
    bus.write_byte_data(ADDR, 0x00, 0x96) # start cycle
    time.sleep(0.5)
    bus.write_byte(ADDR, 0x00)
    data = bus.read_byte(ADDR)
    if (data & 0x20) == 0:
        print "Cycle not ready"
        sys.exit(1)
    bus.write_byte(ADDR, 0x12)
    b2 = bus.read_byte(ADDR)
    bus.write_byte(ADDR, 0x13)
    b1 = bus.read_byte(ADDR)
    bus.write_byte(ADDR, 0x14)
    b0 = bus.read_byte(ADDR)
    return ((b2 << 16) + (b1 << 8) + b0)

def main():
    ch = int(sys.argv[1])
    print "Using bus %d" % ch
    bus = smbus.SMBus(ch % 2)

    bus.write_byte_data(ADDR, 0x00, 0x01) # hold register reset
    time.sleep(0.1)
    bus.write_byte_data(ADDR, 0x00, 0x02) # release register reset, power up digital
    time.sleep(0.1)
    bus.write_byte(ADDR, 0x00) # read register 0
    data = bus.read_byte(ADDR)
    if (data & 0x08) == 0:
        print "Power up timed out"
        sys.exit(1)
    bus.write_byte_data(ADDR, 0x00, 0x82) # internal LDO, power up digital
    bus.write_byte_data(ADDR, 0x01, 0x01) # PGA gain 2x for temperature sensor
    bus.write_byte_data(ADDR, 0x15, 0x30) # CLK_CHP off
    bus.write_byte_data(ADDR, 0x00, 0x86) # internal LDO, power up analog, power up digital

    while True:

        # measure temperature
        bus.write_byte_data(ADDR, 0x1B, 0x00) # PGA bypass disable
        bus.write_byte_data(ADDR, 0x11, 0x02) # Switch to temperature sensor
        # 109 mV at 25C, 0.360 mV per degree C
        # T = V / 0.00036 - 277.78
        r = get_reading(bus)
        v = 4.5 * float(r) / float(2**24)
        t = v / float(0.00036) - 277.78

        # measure voltages
        bus.write_byte_data(ADDR, 0x1B, 0x10) # PGA bypass enable
        bus.write_byte_data(ADDR, 0x11, 0x00) # Switch to inputs
        bus.write_byte_data(ADDR, 0x02, 0x00) # Ch1
        r1 = get_reading(bus)
        bus.write_byte_data(ADDR, 0x02, 0x80) # Ch2
        r2 = get_reading(bus)
        v1 = 9 * float(r1) / float(2**24)
        v2 = 9 * float(r2) / float(2**24)
        vtot = v1 + v2 + OFFSETS[ch]

        # print results
        print "t=%.1f v1=%.3f v2=%.3f vtot=%.3f" % (t, v1, v2, vtot)

if __name__== "__main__":
    main()
