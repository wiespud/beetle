'''
Interface to cooling system for tracton motor controller

Uses DS18B20 and DROK PWM motor controller to control
fan mounted to heatsink of traction motor controller

DROK PWM signal frequency range: 0 ~ 100KHz (recommend 20KHz)
https://gpiozero.readthedocs.io/en/stable/api_output.html#pwmoutputdevice

With out1 going to black fan wire and out2 going to blue, set in1 high and in2 low to suck air from the open side to the guarded side
'''

import gpiozero

import ds

ADDRESS = '' # XXX TODO fill in address of appropriate DS18B20 here
PWM_PIN = '' # XXX TODO
EN_PIN = '' # XXX TODO
PWM_STEP = 5

class Cooling:
    ''' Motor controller cooling '''
    def __init__(self,
                 address=ADDRESS,
                 pwm_pin=PWM_PIN,
                 enable_pin=EN_PIN,
                 target=40,
                 warning=60.0,
                 error=80.0,
                 emergency=100.0):
        self.address = address
        self.pwm = gpiozero.PWMOutputDevice(pwm_pin, frequency=20000)
        self.enable_pin = gpiozero.LED(enable_pin, active_high=False)
        self.target = target
        self.warning = warning
        self.error = error
        self.emergency = emergency
        self.on = False
        self.last_temp = 0.0
        self.pwm_value = 0
        self.pwm.value = float(self.pwm_value) / 100.0

    def update_cooling(self):
        self.last_temp = ds.get_temp(self.address)
        temp = round(self.last_temp)
        if temp > self.target:
            if self.pwm_value < 100:
                self.pwm_value += PWM_STEP
                self.pwm.value = float(self.pwm_value) / 100.0
            if not self.on:
                self.pwm.on()
                self.enable_pin.on()
                self.on = True
        elif temp < self.target:
            if self.pwm_value > 0:
                self.pwm_value -= PWM_STEP
                self.pwm.value = float(self.pwm_value) / 100.0
            if self.on and self.pwm_value == 0.0:
                self.pwm.off()
                self.enable_pin.off()
                self.on = False

    def get_last_temp(self):
        return self.last_temp

    def get_pwm_duty(self):
        return self.pwm_value
