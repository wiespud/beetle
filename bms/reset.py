#!/usr/bin/env python

import smbus
import sys
import time

# 1-8  is at 6.925
# 9-16 is at 6.945

ADDR_NAU = 0x2a
TCA = {
    0x70: {
        0: { 'offset': -0.065 },
        1: { 'offset': -0.050 },
        2: { 'offset': -0.075 },
        3: { 'offset': -0.077 },
    },
    0x71: {
        0: { 'offset': -0.074 },
        1: { 'offset': -0.057 },
        2: { 'offset': -0.022 },
        3: { 'offset': -0.013 },
    },
    0x72: {
        0: { 'offset': -0.027 },
        1: { 'offset': -0.032 },
        2: { 'offset': -0.019 },
        3: { 'offset': -0.004 },
    },
    0x73: {
        0: { 'offset': -0.000 },
        1: { 'offset': 0.003 },
        2: { 'offset': -0.015 },
        3: { 'offset': 0.010 },
    },
}

def nau_setup(bus):
    bus.write_byte_data(ADDR_NAU, 0x00, 0x01) # hold register reset
    time.sleep(0.1)
    bus.write_byte_data(ADDR_NAU, 0x00, 0x02) # release register reset, power up digital
    time.sleep(0.1)
    bus.write_byte(ADDR_NAU, 0x00) # read register 0
    data = bus.read_byte(ADDR_NAU)
    if (data & 0x08) == 0:
        print "Power up timed out"
        return False
    bus.write_byte_data(ADDR_NAU, 0x00, 0x82) # internal LDO, power up digital
    bus.write_byte_data(ADDR_NAU, 0x01, 0x01) # PGA gain 2x for temperature sensor
    bus.write_byte_data(ADDR_NAU, 0x15, 0x30) # CLK_CHP off
    bus.write_byte_data(ADDR_NAU, 0x00, 0x86) # internal LDO, power up analog, power up digital
    return True

def main():
    # ch = int(sys.argv[1])
    # print "Using bus %d" % ch
    bus = smbus.SMBus(1)

    # Make sure all switches are disabled to start with
    for addr in TCA:
        for ch in TCA[addr]:
            bus.write_byte(addr, 0)

    # Set up ADCs
    for addr in TCA:
        for ch in TCA[addr]:
            bus.write_byte(addr, 1 << ch)
            if not nau_setup(bus):
                print "Setup failed on TCA 0x%02X, ch %d" % (addr, ch)
                sys.exit(1)
        bus.write_byte(addr, 0)

if __name__== "__main__":
    main()
