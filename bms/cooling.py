'''
Interface to cooling system for tracton motor controller

Uses DS18B20 and DROK PWM motor controller to control
fan mounted to heatsink of traction motor controller

DROK PWM signal frequency range: 0 ~ 100KHz (recommend 20KHz)
https://gpiozero.readthedocs.io/en/stable/api_output.html#pwmoutputdevice
'''

import gpiozero

import ds

ADDRESS = '' # XXX TODO fill in address of appropriate DS18B20 here
PWM_PIN = '' # XXX TODO
EN_PIN = '' # XXX TODO
PWM_STEP = 0.05

class Cooling:
    ''' Motor controller cooling '''
    def __init__(self,
                 address=ADDRESS,
                 pwm_pin=PWM_PIN,
                 enable_pin=EN_PIN,
                 target=40.0,
                 warning=60.0,
                 error=80.0,
                 emergency=100.0):
        self.address = address
        self.pwm_pin = gpiozero.PWMOutputDevice(pwm_pin, frequency=20000)
        self.enable_pin = gpiozero.LED(enable_pin, active_high=False)
        self.target = target
        self.warning = warning
        self.error = error
        self.emergency = emergency
        self.on = False

    def update_cooling(self):
        temp = round(ds.get_temp(self.address))
        if temp > self.target:
            if self.pwm_pin.value < 1.0:
                self.pwm_pin.value += PWM_STEP
            if not self.on:
                self.pwm_pin.on()
                self.enable_pin.on()
                self.on = True
        elif temp < self.target:
            if self.pwm_pin.value > 0.0:
                self.pwm_pin.value -= PWM_STEP
            if self.on and self.pwm_pin.value == 0.0:
                self.pwm_pin.off()
                self.enable_pin.off()
                self.on = False
