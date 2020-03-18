#!/usr/bin/env python

import gpiozero
import subprocess
import sys
import time

from datetime import datetime

ON_TEMP = 17.5
OFF_TEMP = 18.0
HOLDOFF = 65.0 # wait this long for data to accumulate before doing anything

class BatteryHeater:
    ''' Battery heater class '''
    def __init__(self, logger, cur):
        self.logger = logger
        self.cur = cur
        self.front_heat = gpiozero.OutputDevice(22, active_high=False)
        self.back_heat = gpiozero.OutputDevice(23, active_high=False)
        self.front_temp = None
        self.back_temp = None
        self.init_time = datetime.now()

    def gather(self):
        ''' get average temperatures from db '''
        if (datetime.now() - self.init_time).total_seconds() < HOLDOFF:
            return

        self.cur.execute('SELECT a.pack, a.ts, a.t_av FROM ( '
                         'SELECT b.*, ROW_NUMBER() OVER (PARTITION BY pack ORDER BY id DESC) AS rn '
                         'FROM history AS b ) AS a WHERE rn = 1')
        now = datetime.now()
        for row in cur.fetchall():
            pack = row[0]
            ts = row[1]
            t = row[2]
            if (now - ts).total_seconds() > HOLDOFF:
                self.logger.error('temperature data is too stale')
                self.front_heat.off()
                self.back_heat.off()
            elif pack == 'front':
                self.front_temp = t
            elif pack == 'back':
                self.back_temp = t
            else:
                self.logger.error('unrecognized pack %s', pack)

    def process(self):
        ''' turn heat on or off based on newly calculated averages '''
        if self.front_temp == None or self.back_temp == None:
            return

        if self.front_temp <= ON_TEMP:
            if self.front_heat.value == 0:
                self.front_heat.on()
                self.logger.info('front heat on')
        elif self.front_temp >= OFF_TEMP:
            if self.front_heat.value == 1:
                self.front_heat.off()
                self.logger.info('front heat off')

        if self.back_temp <= ON_TEMP:
            if self.back_heat.value == 0:
                self.back_heat.on()
                self.logger.info('back heat on')
        elif self.back_temp >= OFF_TEMP:
            if self.back_heat.value == 1:
                self.back_heat.off()
                self.logger.info('back heat off')

# ~ FRONT_TEMP_CMD = 'ssh beetle-front.local tail /home/pi/beetle/bms/charge.log | grep t_av | tail -1'
# ~ BACK_TEMP_CMD = 'tail /home/pi/beetle/bms/charge.log | grep t_av | tail -1'

# ~ LOG = open('heating.log', 'a+', buffering=1)

# ~ def log_print(str):
    # ~ ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    # ~ print '%s %s' % (ts, str)
    # ~ LOG.write('%s %s\n' % (ts, str))

# ~ def main():

    # ~ # Setup battery heaters
    # ~ front_heat = gpiozero.OutputDevice(22, active_high=False)
    # ~ back_heat = gpiozero.OutputDevice(23, active_high=False)

    # ~ front_prev = None
    # ~ back_prev = None
    # ~ while True:

        # ~ retries=300
        # ~ while retries > 0:
            # ~ retries -= 1
            # ~ if retries < 1:
                # ~ log_print('Exiting due to too many retries')
                # ~ sys.exit(1)
            # ~ try:
                # ~ front_temp_str = subprocess.check_output(FRONT_TEMP_CMD, shell=True)
                # ~ back_temp_str = subprocess.check_output(BACK_TEMP_CMD, shell=True)
                # ~ front_temp = float(front_temp_str.split(' ')[3])
                # ~ back_temp = float(back_temp_str.split(' ')[3])
            # ~ except ValueError:
                # ~ log_print('Error converting front_temp=%s back_temp=%s' % (front_temp_str, back_temp_str))
                # ~ continue
            # ~ if front_temp_str == front_prev:
                # ~ log_print('Error: front stuck at %s' % front_temp_str)
                # ~ continue
            # ~ if back_temp_str == back_prev:
                # ~ log_print('Error: back stuck at %s' % back_temp_str)
                # ~ continue
            # ~ break

        # ~ front_prev = front_temp_str
        # ~ back_prev = back_temp_str

        # ~ if front_temp <= ON_TEMP:
            # ~ if front_heat.value == 0:
                # ~ front_heat.on()
                # ~ log_print('front on')
        # ~ elif front_temp >= OFF_TEMP:
            # ~ if front_heat.value == 1:
                # ~ front_heat.off()
                # ~ log_print('front off')

        # ~ if back_temp <= ON_TEMP:
            # ~ if back_heat.value == 0:
                # ~ back_heat.on()
                # ~ log_print('back on')
        # ~ elif back_temp >= OFF_TEMP:
            # ~ if back_heat.value == 1:
                # ~ back_heat.off()
                # ~ log_print('back off')

        # ~ time.sleep(60)

# ~ if __name__== '__main__':
    # ~ main()
