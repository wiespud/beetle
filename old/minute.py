#!/usr/bin/env python

import gpiozero
import time

def main():
    load1 = gpiozero.LED(20, active_high=False)
    load2 = gpiozero.LED(21, active_high=False)
    load1.on()
    load2.on()
    time.sleep(10)
    load1.off()
    load2.off()

if __name__== "__main__":
    main()
