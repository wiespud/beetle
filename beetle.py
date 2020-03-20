#!/usr/bin/env python

import logging
import MySQLdb
import socket
import time

from datetime import datetime
from logging.handlers import RotatingFileHandler
from multiprocessing import Process

import bms
import heating

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
        self.bms = bms.BatteryMonitoringSystem(self.logger, self.db, location)
        if location == 'back':
            self.heat = heating.BatteryHeater(self.logger, self.cur)

    def as_often_as_possible(self):
        ''' Do these tasks as often as possible '''
        self.bms.as_often_as_possible()

    def every_minute(self):
        ''' Do these tasks once a minute '''
        self.bms.every_minute()
        self.heat.every_minute()

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

    # The location of the pi determines what its responsibilities are.
    # The hostname is beetle-location.
    location = socket.gethostname().split('-')[1]

    beetle = Beetle(location)
    beetle.poll()

if __name__== '__main__':
    main()
