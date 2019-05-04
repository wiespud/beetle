#!/usr/bin/env python

import smbus

import batteries

def main():
    bus = smbus.SMBus(1)
    batts = batteries.Batteries(bus)
    while True:
        batts.do_measurements()
        print ''
        for batt in batts.battery_iter():
            g = batt.get_group()
            t = batt.get_last_temperature()
            t_av = batt.get_average_temperature()
            v = batt.get_last_voltage()
            v_av = batt.get_average_voltage()
            print 'Group %2d: t=%.01f (%.01f) v=%.03f (%.03f)' % (g, t, t_av, v, v_av)

if __name__== '__main__':
    main()
