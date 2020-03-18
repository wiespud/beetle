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

def setup_db_cur(location):
    if location == 'back':
        host = 'localhost'
    else:
        host = '10.10.10.2'
    with open('db_passwd.txt') as fin:
        passwd = fin.read()
    db = MySQLdb.connect(host=host, user='beetle', passwd=passwd, db='beetle')
    return db.cursor()

class Beetle:
    ''' Integration class for all the components of the car '''
    def __init__(self, location):
        self.location = location
        self.logger = setup_logger('beetle')
        self.cur = setup_db_cur(location)
        self.bms = bms.BatteryMonitoringSystem(self.logger, self.cur)
        self.heat = heating.BatteryHeater(self.logger, self.cur)

    def gather(self):
        ''' Gather information locally and from other pi '''
        self.bms.gather()
        # ~ self.heat.gather()

    def process(self):
        ''' Process gathered information and take actions '''
        self.bms.process()
        # ~ self.heat.process()

    def poll(self):
        ''' Repeat gather and process forever '''
        while True:
            gather()
            process()
            time.sleep(5)

def main():

    # The location of the pi determines what its responsibilities are.
    # The hostname is beetle-location.
    location = socket.gethostname().split('-')[1]

    # The bms data collection needs to run as a separate process.
    logger = setup_logger('bms')
    cur = setup_db_cur(location)
    bms_proc = Process(target=bms.poll, args=(location, logger, cur,))
    bms_proc.start()

    beetle = Beetle(location)
    beetle.poll()

if __name__== '__main__':
    main()
