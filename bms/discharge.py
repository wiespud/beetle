#!/usr/bin/env python

import gpiozero
import os
import smbus
import sys
import time

import batteries

def get_data(batts, group):
    batts.do_measurements()
    for batt in batts.battery_iter():
        v = batt.get_last_voltage()
        v_av = batt.get_average_voltage()
        if batt.get_group() == group:
            return (v, v_av)

def main():
    print 'Discharging group %s using load %s' % (sys.argv[1], sys.argv[2])
    group = int(sys.argv[1])
    gpio_num = 19 + int(sys.argv[2])
    i2c_num = int(sys.argv[2]) % 2
    load = gpiozero.LED(gpio_num, active_high=False)
    bus = smbus.SMBus(i2c_num)
    batts = batteries.Batteries(bus)
    while True:
        v, v_av = get_data(batts, group)
        print 'Group %2d: v=%.03f (%.03f)' % (group, v, v_av)

if __name__== "__main__":
    main()
