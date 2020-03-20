#!/usr/bin/env python

import gpiozero
import time
import smtplib
import sys

from email.MIMEMultipart import MIMEMultipart
from email.MIMEText import MIMEText

ON_TIME = 60
MIN_OFF_TIME = 60
COMPLETION_TIME = 60 * 60

GPIO_DEFS = {
    "1": {
        "green": 5,
        "red": 6,
        "load": 20,
    },
    "2": {
        "green": 13,
        "red": 19,
        "load": 21,
    },
}

def main():
    battery = sys.argv[1]
    battery_number = sys.argv[2]
    if battery not in GPIO_DEFS:
        print "Battery %s not recognized" % battery
        sys.exit(1)
    green = gpiozero.Button(GPIO_DEFS[battery]["green"])
    red = gpiozero.Button(GPIO_DEFS[battery]["red"])
    load = gpiozero.LED(GPIO_DEFS[battery]["load"], active_high=False)
    discharge_time = 0
    timer = start_time = time.time()
    while (time.time() - timer) < COMPLETION_TIME:
        if green.is_pressed and not red.is_pressed:
            load.on()
            time.sleep(ON_TIME)
            load.off()
            discharge_time += ON_TIME
            timer = time.time()
            time.sleep(MIN_OFF_TIME)
        else:
            time.sleep(1)
    body = "battery: %s\ntotal: %s\ndischarge: %s" % (battery_number, int(time.time() - start_time), discharge_time)
    print body
    addr = "michaelwaynejohns@gmail.com"
    msg = MIMEMultipart()
    msg['From'] = addr
    msg['To'] = addr
    msg['Subject'] = "tester %s done" % battery
    msg.attach(MIMEText(body, 'plain'))
    text = msg.as_string()
    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    server.login(addr, "LongL4shes")
    server.sendmail(addr, addr, text)
    server.quit()

if __name__== "__main__":
    main()
