'''
Interface to monitor 12V accessory battery and enable DCDC converter
'''

import gpiozero

class Cooling:
    ''' ADCDCDC converter '''
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
