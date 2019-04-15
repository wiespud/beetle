#!/usr/bin/env python

import smbus
import sys
import time

ADDR_NAU = 0x2a
TCA = {
    0x70: {
        0: { 'offset': -0.055 },
        1: { 'offset': -0.043 },
        2: { 'offset': -0.059 },
        3: { 'offset': -0.078 },
    },
    0x71: {
        0: { 'offset': -0.036 },
        1: { 'offset': -0.058 },
        2: { 'offset': 0.010 },
        3: { 'offset': 0.011 },
    },
    # 0x72: {
    #     0: { 'offset': 0.0 },
    #     1: { 'offset': 0.0 },
    #     2: { 'offset': 0.0 },
    #     3: { 'offset': 0.0 },
    # },
    # 0x73: {
    #     0: { 'offset': 0.0 },
    #     1: { 'offset': 0.0 },
    #     2: { 'offset': 0.0 },
    #     3: { 'offset': 0.0 },
    # },
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

def get_reading(bus):
    # bus.write_byte_data(ADDR_NAU, 0x00, 0x96) # start cycle
    # time.sleep(0.5)
    bus.write_byte(ADDR_NAU, 0x00)
    data = bus.read_byte(ADDR_NAU)
    if (data & 0x20) == 0:
        print "Cycle not ready"
        sys.exit(1)
    bus.write_byte(ADDR_NAU, 0x12)
    b2 = bus.read_byte(ADDR_NAU)
    bus.write_byte(ADDR_NAU, 0x13)
    b1 = bus.read_byte(ADDR_NAU)
    bus.write_byte(ADDR_NAU, 0x14)
    b0 = bus.read_byte(ADDR_NAU)
    return ((b2 << 16) + (b1 << 8) + b0)

def main():
    # ch = int(sys.argv[1])
    # print "Using bus %d" % ch
    bus = smbus.SMBus(1)

    # Set up ADCs
    for addr in TCA:
        for ch in TCA[addr]:
            bus.write_byte(addr, 1 << ch)
            if not nau_setup(bus):
                print "Setup failed on TCA 0x%02X, ch %d" % (addr, ch)
                sys.exit(1)
        bus.write_byte(addr, 0)

    while True:
        for addr in TCA:

            # Broadcast temperature setup and start cycle
            bus.write_byte(addr, 0xf)
            bus.write_byte_data(ADDR_NAU, 0x1B, 0x00) # PGA bypass disable
            bus.write_byte_data(ADDR_NAU, 0x11, 0x02) # Switch to temperature sensor
            bus.write_byte_data(ADDR_NAU, 0x00, 0x96) # Start cycle
            time.sleep(0.5)

            # Get each temperature reading
            for ch in TCA[addr]:
                bus.write_byte(addr, 1 << ch)
                r = get_reading(bus)
                v = 4.5 * float(r) / float(2**24)
                TCA[addr][ch]['t'] = v / float(0.00036) - 277.78

            # Broadcast ADC setup, ch1 selection, and start cycle
            bus.write_byte(addr, 0xf)
            bus.write_byte_data(ADDR_NAU, 0x1B, 0x10) # PGA bypass enable
            bus.write_byte_data(ADDR_NAU, 0x11, 0x00) # Switch to inputs
            bus.write_byte_data(ADDR_NAU, 0x02, 0x00) # Ch1
            bus.write_byte_data(ADDR_NAU, 0x00, 0x96) # Start cycle
            time.sleep(0.5)

            # Get each ch1 reading
            for ch in TCA[addr]:
                bus.write_byte(addr, 1 << ch)
                r = get_reading(bus)
                TCA[addr][ch]['v1'] = 9 * float(r) / float(2**24)

            # Broadcast ch2 selection, and start cycle
            bus.write_byte(addr, 0xf)
            bus.write_byte_data(ADDR_NAU, 0x02, 0x80) # Ch2
            bus.write_byte_data(ADDR_NAU, 0x00, 0x96) # Start cycle
            time.sleep(0.5)

            # Get each ch2 reading
            for ch in TCA[addr]:
                bus.write_byte(addr, 1 << ch)
                r = get_reading(bus)
                TCA[addr][ch]['v2'] = 9 * float(r) / float(2**24)

            # Disable all channels before moving on to next TCA
            bus.write_byte(addr, 0)

        for addr in TCA:
            for ch in TCA[addr]:
                t = TCA[addr][ch]['t']
                v1 = TCA[addr][ch]['v1']
                v2 = TCA[addr][ch]['v2']
                v = v1 + v2 + TCA[addr][ch]['offset']
                print 'TCA 0x%02X, ch %d: t=%.1f v=%.3f (v1=%.3f v2=%.3f)' % (addr, ch, t, v, v1, v2)
        print ''

if __name__== "__main__":
    main()
