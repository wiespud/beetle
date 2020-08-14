'''
Interface to monitor battery temperatures and turn on battery heaters
'''

import gpiozero
import time

from datetime import datetime

ON_TEMP = 19.5
OFF_TEMP = 20.0
HOLDOFF = 90.0 # wait this long for data to accumulate before doing anything

class BatteryHeater:
    ''' Battery heater class '''
    def __init__(self, beetle):
        self.beetle = beetle
        self.front_heat = gpiozero.OutputDevice(22, active_high=False)
        self.back_heat = gpiozero.OutputDevice(23, active_high=False)
        self.init_time = time.time()
        self.last_poll = 0.0
        self.beetle.logger.info('Battery heater poller initialized')

    def poll(self):
        ''' no battery heaters without AC power '''
        if self.beetle.gpio.get('ac_present') == 0:
            if self.front_heat.value == 1:
                self.front_heat.off()
                self.beetle.logger.info('front heat off (AC power lost)')
            if self.back_heat.value == 1:
                self.back_heat.off()
                self.beetle.logger.info('back heat off (AC power lost)')
            return
        ''' don't start until data has accumulated '''
        now = time.time()
        if now - self.init_time < HOLDOFF:
            return
        ''' once a minute '''
        delta = now - self.last_poll
        if delta < 60.0 and delta > 0.0:
            return
        self.last_poll = now
        if now - self.beetle.bms.last_poll > HOLDOFF:
            self.beetle.logger.error('temperature data is too stale')
            self.front_heat.off()
            self.back_heat.off()
            return
        ''' turn heat on or off based on average temperatures from bms '''
        if self.beetle.bms.front_t_av <= ON_TEMP:
            if self.front_heat.value == 0:
                self.front_heat.on()
                self.beetle.logger.info('front heat on')
        elif self.beetle.bms.front_t_av >= OFF_TEMP:
            if self.front_heat.value == 1:
                self.front_heat.off()
                self.beetle.logger.info('front heat off')

        if self.beetle.bms.back_t_av <= ON_TEMP:
            if self.back_heat.value == 0:
                self.back_heat.on()
                self.beetle.logger.info('back heat on')
        elif self.beetle.bms.back_t_av >= OFF_TEMP:
            if self.back_heat.value == 1:
                self.back_heat.off()
                self.beetle.logger.info('back heat off')
