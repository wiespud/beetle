#!/usr/bin/env python

import gpiozero
import subprocess
import sys
import time

from datetime import datetime

ON_TEMP = 17.5
OFF_TEMP = 18.0
FRONT_TEMP_CMD = 'ssh beetle-front.local tail /home/pi/beetle/bms/charge.log | grep t_av | tail -1'
BACK_TEMP_CMD = 'tail /home/pi/beetle/bms/charge.log | grep t_av | tail -1'

LOG = open('heating.log', 'a+', buffering=1)

def log_print(str):
    ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print '%s %s' % (ts, str)
    LOG.write('%s %s\n' % (ts, str))

def main():

    # Setup battery heaters
    front_heat = gpiozero.OutputDevice(22, active_high=False)
    back_heat = gpiozero.OutputDevice(23, active_high=False)

    front_prev = None
    back_prev = None
    while True:

        retries=300
        while retries > 0:
            retries -= 1
            if retries < 1:
                log_print('Exiting due to too many retries')
                sys.exit(1)
            try:
                front_temp_str = subprocess.check_output(FRONT_TEMP_CMD, shell=True)
                back_temp_str = subprocess.check_output(BACK_TEMP_CMD, shell=True)
                front_temp = float(front_temp_str.split(' ')[3])
                back_temp = float(back_temp_str.split(' ')[3])
            except ValueError:
                log_print('Error converting front_temp=%s back_temp=%s' % (front_temp_str, back_temp_str))
                continue
            if front_temp_str == front_prev:
                log_print('Error: front stuck at %s' % front_temp_str)
                continue
            if back_temp_str == back_prev:
                log_print('Error: back stuck at %s' % back_temp_str)
                continue
            break

        front_prev = front_temp_str
        back_prev = back_temp_str

        if front_temp <= ON_TEMP:
            if front_heat.value == 0:
                front_heat.on()
                log_print('front on')
        elif front_temp >= OFF_TEMP:
            if front_heat.value == 1:
                front_heat.off()
                log_print('front off')

        if back_temp <= ON_TEMP:
            if back_heat.value == 0:
                back_heat.on()
                log_print('back on')
        elif back_temp >= OFF_TEMP:
            if back_heat.value == 1:
                back_heat.off()
                log_print('back off')

        time.sleep(60)

if __name__== '__main__':
    main()
