#!/usr/bin/env python

import gpiozero
import subprocess
import time

from datetime import datetime

ON_TEMP = 19.0
OFF_TEMP = 19.5
FRONT_TEMP_CMD = 'ssh beetle-front.local tail /home/pi/beetle/bms/charge.log | grep t_av | tail -1 | cut -d \' \' -f4'
BACK_TEMP_CMD = 'tail /home/pi/beetle/bms/charge.log | grep t_av | tail -1 | cut -d \' \' -f4'

LOG = open('heating.log', 'a+', buffering=1)

def log_print(str):
    ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print '%s %s' % (ts, str)
    LOG.write('%s %s\n' % (ts, str))

def main():

    # Setup battery heaters
    front_heat = gpiozero.OutputDevice(22, active_high=False)
    back_heat = gpiozero.OutputDevice(23, active_high=False)

    while True:

        front_temp = float(subprocess.check_output(FRONT_TEMP_CMD, shell=True))
        back_temp = float(subprocess.check_output(BACK_TEMP_CMD, shell=True))

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
