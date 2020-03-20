#!/usr/bin/env python

import gpiozero
import subprocess
import sys
import time

from datetime import datetime

ON_TEMP = 19.5
OFF_TEMP = 20.0
HOLDOFF = 90.0 # wait this long for data to accumulate before doing anything

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

    def every_minute(self):
        ''' Do these tasks once a minute '''
        self.gather()
        self.process()

    def gather(self):
        ''' get average temperatures from db '''
        if (datetime.now() - self.init_time).total_seconds() < HOLDOFF:
            return

        self.cur.execute('SELECT ts, front_t_av, back_t_av FROM history ORDER BY id DESC LIMIT 1')
        now = datetime.now()
        for row in self.cur.fetchall():
            ts = row[0]
            if (now - ts).total_seconds() > HOLDOFF:
                self.logger.error('temperature data is too stale')
                self.front_heat.off()
                self.back_heat.off()
                self.front_temp = None
                self.back_temp = None
            else:
                self.front_temp = row[1]
                self.back_temp = row[2]

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
