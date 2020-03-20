#!/usr/bin/env python

import gpiozero
import os
import smbus
import sys
import time

from datetime import datetime

import batteries

V_TERM = 6.5
T_ON = 30.0
T_COMPLETE = 3600.0 # one hour

LOG = open('discharge.log', 'a+', buffering=1)

def log_print(str):
    ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print '%s %s' % (ts, str)
    LOG.write('%s %s\n' % (ts, str))

def loads_off(loads):
    for group in loads:
        loads[group].off()

def main():
    loads = {}
    state = {} # set to True to indicate load is on
    times = {} # the time the load was last turned on or off
    complete = {} # set to True to indicate discharge completion
    for i in range(1, 3):
        group = int(sys.argv[i])
        gpio_num = 19 + i
        load = gpiozero.LED(gpio_num, active_high=False)
        loads[group] = load
        state[group] = False
        times[group] = time.time()
        complete[group] = False
        log_print('Discharging group %d to %.03fV using load %d' % (group, V_TERM, i))
    bus = smbus.SMBus(1)
    batts = batteries.Batteries(bus)

    # Prime the pump
    for i in range(10):
        batts.do_measurements()

    completion_count = 0
    while completion_count < 2:
        batts.do_measurements()
        ts = time.time()
        for group in loads:
            batt = batts.get_battery(group)
            if batt.check_error_history():
                log_print('ERROR: group %d exceeded error limit' % group)
                loads_off(loads)
                sys.exit(1)
            v = batt.get_last_voltage()
            v_av = batt.get_average_voltage()
            t_diff = ts - times[group]
            if state[group]:
                # Load is on
                if v < V_TERM and t_diff > T_ON:
                    loads[group].off()
                    state[group] = False
                    times[group] = ts
            elif not complete[group]:
                # Load is off
                if t_diff < T_COMPLETE:
                    # Load hasn't been off long enough to consider the discharge complete
                    if v_av > V_TERM:
                        loads[group].on()
                        state[group] = True
                        times[group] = ts
                else:
                    # Load has been off long enough to consider the discharge complete
                    complete[group] = True
                    completion_count += 1
            log_print('group=%2d v=%.03f v_av=%.03f t_diff=%d load_on=%s complete=%s' % (group, v, v_av, t_diff, state[group], complete[group]))

if __name__== "__main__":
    main()
    LOG.close()
