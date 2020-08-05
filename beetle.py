#!/usr/bin/env python

import gpiozero
import logging
import MySQLdb
import socket
import time

from datetime import datetime
from logging.handlers import RotatingFileHandler
from multiprocessing import Process

import bms
import gps
import heating
import state

def setup_logger(name):
    formatter = logging.Formatter(fmt='%(asctime)s %(levelname)-8s %(message)s',
                                  datefmt='%Y-%m-%d %H:%M:%S')
    handler = RotatingFileHandler('/var/log/beetle/%s.log' % name,
                                  maxBytes=1024*1024, backupCount=5)
    handler.setFormatter(formatter)
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    logger.addHandler(handler)
    return logger

def setup_db(location):
    if location == 'back':
        host = 'localhost'
    else:
        host = '10.10.10.2'
    with open('db_passwd.txt') as fin:
        passwd = fin.read()
    db = MySQLdb.connect(host=host, user='beetle', passwd=passwd, db='beetle')
    return db

class Beetle:
    ''' Integration class for all the components of the car '''
    def __init__(self, location):
        self.location = location
        self.logger = setup_logger('beetle')
        self.db = setup_db(location)
        self.cur = self.db.cursor()
        if location == 'back':
            self.heat = heating.BatteryHeater(self)
            self.dash_light = gpiozero.OutputDevice(27, active_high=False)
            self.dash_light.on() # this turns the light off
            self.ac_present = gpiozero.InputDevice(4, pull_up=True)
            self.ignition = gpiozero.InputDevice(24, pull_up=True)
            self.charging = gpiozero.InputDevice(12, pull_up=True)
            self.charger = gpiozero.OutputDevice(5, active_high=False)
            self.dcdc = gpiozero.OutputDevice(13, active_high=False)
        else: # self.location == 'front':
            self.gps = gps.GPS(self)
        self.bms = bms.BatteryMonitoringSystem(self)
        self.state = state.State(self)

    def as_often_as_possible(self):
        ''' Do these tasks as often as possible '''
        self.bms.as_often_as_possible()
        if self.location == 'back':
            # XXX for now just keep the dcdc on all the time when driving
            if self.ac_present.value == 0 and self.ignition.value == 1 and self.dcdc.value == 0:
                self.logger.info('turning on dcdc')
                self.dcdc.on()
            elif (self.ac_present.value == 1 or self.ignition.value == 0) and self.dcdc.value == 1:
                self.logger.info('turning off dcdc')
                self.dcdc.off()
        else: # self.location == 'front':
            self.gps.as_often_as_possible()

    def every_minute(self):
        ''' Do these tasks once a minute (back only)'''
        self.bms.every_minute()
        self.heat.every_minute()
        charger_state = self.state.get('charger')
        if (charger_state == 'enabled' and self.charger.value == 0):
            self.logger.info('enabling charger')
            self.charger.on()
        elif (charger_state == 'disabled' and self.charger.value == 1):
            self.logger.info('disabling charger')
            self.charger.off()

        # XXX enable/disable wifi using `sudo ip link set down/up wlan0` based on ac_present and eventually gps maybe?

    def poll(self):
        ''' Repeat tasks forever at desired frequences '''
        prev_ts = datetime.now()
        while True:
            self.as_often_as_possible()
            ts = datetime.now()
            if self.location == 'back' and ts.minute != prev_ts.minute:
                self.every_minute()
                prev_ts = ts

def main():

    # Wait a minute for networking, mysql, etc. to start
    time.sleep(60)

    # The location of the pi determines what its responsibilities are.
    # The hostname is beetle-location.
    location = socket.gethostname().split('-')[1]

    beetle = Beetle(location)
    beetle.poll()

if __name__== '__main__':
    main()
