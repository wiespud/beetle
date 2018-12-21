#!/usr/bin/env python

import gpiozero
import os
import smbus
import sys
import time

V_END = 6.0
T_END = 60.0

ADDR = 0x2a
BUS = 1

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

def main():
    b1 = sys.argv[1]
    b2 = sys.argv[2]
    print "b1=%s b2=%s" % (b1, b2)

    # Set up logging
    log1_path = "/home/pi/beetle/bms/discharge_logs/%s.log" % b1
    log2_path = "/home/pi/beetle/bms/discharge_logs/%s.log" % b2
    if os.path.isfile(log1_path):
        print "%s already exists" % log1_path
        sys.exit(1)
    if os.path.isfile(log2_path):
        print "%s already exists" % log2_path
        sys.exit(1)
    log1 = open(log1_path, "w+")
    log2 = open(log2_path, "w+")

    # Set up I2C
    bus = smbus.SMBus(BUS)
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

    # Set up loads
    load1 = gpiozero.LED(20, active_high=False)
    load2 = gpiozero.LED(21, active_high=False)

    # Start discharge test
    start_time = time.time()
    start_loads = True
    test1_live = True
    test2_live = True
    test1_end_time = 0
    test2_end_time = 0

    while test1_live or test2_live:
        # Turn on loads after readings stabilize
        if start_loads and (time.time() > (start_time + 60)):
            load1.on()
            load2.on()
            start_loads = False

        # Battery 1
        if test1_live:
            bus.write_byte_data(ADDR, 0x02, 0x00) # Ch1
            t1 = time.time() - start_time
            r1 = get_reading(bus)
            v1 = 18.335 * float(r1) / float(2**24)
            log1.write("%.2f\t%.3f\n" % (t1, v1))
            log1.flush()
            if v1 < V_END:
                if test1_end_time == 0:
                    test1_end_time = time.time()
                if time.time() > (test1_end_time + T_END):
                    load1.off()
                    test1_live = False
                    log1.close()
                    print "Battery 1 complete"
            else:
                test1_end_time = 0
        else:
            time.sleep(0.5)
        time.sleep(2)

        #Battery 2
        if test2_live:
            bus.write_byte_data(ADDR, 0x02, 0x80) # Ch2
            t2 = time.time() - start_time
            r2 = get_reading(bus)
            v2 = 18.298 * float(r2) / float(2**24)
            log2.write("%.2f\t%.3f\n" % (t2, v2))
            log2.flush()
            if v2 < V_END:
                if test2_end_time == 0:
                    test2_end_time = time.time()
                if time.time() > (test2_end_time + T_END):
                    load2.off()
                    test2_live = False
                    log2.close()
                    print "Battery 2 complete"
            else:
                test2_end_time = 0
        else:
            time.sleep(0.5)
        time.sleep(2)

    print "Test complete"
    sys.exit(0)

if __name__== "__main__":
    main()
