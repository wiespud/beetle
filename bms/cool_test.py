#!/usr/bin/env python

import gpiozero
import time

import cooling
import ds

def main():
    in1 = gpiozero.LED(23, active_high=False)
    in1.off()

    cool = cooling.Cooling(address='28-000003c72bff',
                           pwm_pin=25,
                           enable_pin=24,
                           target=20)

    while True:
        cool.update_cooling()
        print cool.get_last_temp(), cool.get_pwm_duty()
        time.sleep(1)

if __name__== '__main__':
    main()
