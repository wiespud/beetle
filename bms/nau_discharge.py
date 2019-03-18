#!/usr/bin/env python

import gpiozero
import os
import smbus
import sys
import time

T_ON = 20.0
T_END = 60.0 * 60.0

NUM_SAMPLES = 10

ADDR = 0x2a
OFFSETS = { 1: -0.077, 2: -0.012 }

def get_reading(bus):
    bus.write_byte_data(ADDR, 0x00, 0x96) # start cycle
    time.sleep(0.5)
    bus.write_byte(ADDR, 0x00)
    data = bus.read_byte(ADDR)
    if (data & 0x20) == 0:
        print "Cycle not ready"
        return 0
    bus.write_byte(ADDR, 0x12)
    b2 = bus.read_byte(ADDR)
    bus.write_byte(ADDR, 0x13)
    b1 = bus.read_byte(ADDR)
    bus.write_byte(ADDR, 0x14)
    b0 = bus.read_byte(ADDR)
    return ((b2 << 16) + (b1 << 8) + b0)

samples = []
index = 0
def get_voltage(bus, ch):
    global samples
    global index
    bus.write_byte_data(ADDR, 0x02, 0x00) # Ch1
    r1 = get_reading(bus)
    bus.write_byte_data(ADDR, 0x02, 0x80) # Ch2
    r2 = get_reading(bus)
    v1 = 9 * float(r1) / float(2**24)
    v2 = 9 * float(r2) / float(2**24)
    v = v1 + v2 + OFFSETS[ch]
    if len(samples) < NUM_SAMPLES:
        samples.append(v)
        return v
    samples[index] = v
    index = (index + 1) % NUM_SAMPLES
    return sum(samples) / NUM_SAMPLES

def main():
    global index
    ch = int(sys.argv[1])
    v_end = float(sys.argv[2])
    print "Using bus/channel %d" % ch
    gpio_num = 19 + ch

    # Set up I2C
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
    bus.write_byte_data(ADDR, 0x1B, 0x10) # PGA bypass enable
    bus.write_byte_data(ADDR, 0x15, 0x30) # CLK_CHP off
    bus.write_byte_data(ADDR, 0x00, 0x86) # internal LDO, power up analog, power up digital
    time.sleep(0.1)

    # Set up load
    load = gpiozero.LED(gpio_num, active_high=False)

    # Find starting voltage
    for i in range(12):
        get_voltage(bus, ch)
    v_start = get_voltage(bus, ch)
    print "Vstart=%.03f Vend=%.03f" % (v_start, v_end)

    # Start discharge test
    start_time = time.time()
    end_timer = time.time()

    print_voltage = True
    flush = 0
    while (time.time() - end_timer) < T_END:
        v = get_voltage(bus, ch)
        flush = flush - 1
        if v > v_end and flush < 0:
            print "V=%.03f - load on" % v
            load.on()
            time.sleep(T_ON)
            load.off()
            print_voltage = True
            flush = NUM_SAMPLES
            end_timer = time.time()
        if print_voltage or index == 0:
            print "ch%d V=%.03f Vstart=%.03f Vend=%.03f" % (ch, v, v_start, v_end)
            print_voltage = False

    print "Test complete"
    sys.exit(0)

if __name__== "__main__":
    main()
