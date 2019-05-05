'''
Interface to measurement state of charge of the traction battery pack

Uses HASS 200-S current sensor and NAU7802SGI ADC to
integrate current over time, estimating state of charge. 
Uses <XXX PWM?> to interface with original gas needle.

https://www.lem.com/sites/default/files/products_datasheets/hass_50_600-s.pdf
'''

import gpiozero
import time

import nau

PWM_PIN = '' # XXX TODO
NAU_CH = 1

class StateOfCharge:
    ''' Battery pack state of charge '''
    def __init__(self, bus, initial_soc=0.0, pin=PWM_PIN):
        self.bus = bus
        self.pwm = gpiozero.PWMOutputDevice(pin)
        self.prev_ts = None
        self.state_of_charge = initial_soc

    def set_needle(self, value):
        if value > 0.0 and self.pwm.value == 0:
            self.pwm.on()
        elif value == 0.0 and self.pwm.value > 0.0:
            self.pwm.off()
        self.pwm.value = value

    def set_soc(self, soc):
        self.state_of_charge = soc

    def update_soc(self):
        nau.voltage_setup(self.bus, NAU_CH)
        nau.start_measurement(self.bus)
        time.sleep(0.5)
        volts = nau.get_voltage(self.bus)
        current = 0.0 # XXX TODO convert volts to current
        ts = time.time()
        # XXX TODO math...
        self.prev_ts = ts