#!/usr/bin/env python

import gpiozero
import gpsd
import logging
import MySQLdb
import os
import socket
import subprocess
import time

from datetime import datetime
from geopy.distance import distance
from logging.handlers import RotatingFileHandler

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

class Charger:
    ''' Charger '''
    def __init__(self, beetle):
        self.beetle = beetle
        self.pin = gpiozero.OutputDevice(5, active_high=False)
        self.last_poll = 0.0
        self.beetle.logger.info('Charger poller initialized')

    def poll(self):
        now = time.time()
        delta = now - self.last_poll
        if delta < 60.0 and delta > 0.0:
            return
        self.last_poll = now
        state = self.beetle.state.get('charger')
        odometer = float(self.beetle.state.get('charge_odometer'))
        charging = self.beetle.gpio.get('charging')
        ''' handle charger disable/enable/one-shot '''
        # TODO: handle switch gpio that hard-enables charger
        if state == 'enabled' and self.pin.value == 0:
            self.beetle.logger.info('enabling charger')
            self.pin.on()
        elif state == 'disabled' and self.pin.value == 1:
            self.beetle.logger.info('disabling charger')
            self.pin.off()
        elif state == 'once' and charging == 0:
            if self.pin.value == 0:
                self.beetle.logger.info('enabling charger for one charge')
                self.pin.on()
            elif self.pin.value == 1:
                self.beetle.logger.info('charge complete, disabling charger')
                self.pin.off()
                self.beetle.state.set('charger', 'disabled')
        ''' reset charge odometer if a charge is in progress '''
        if charging == 1 and odometer > 0.0:
            self.beetle.state.set('charge_odometer', '0.0')

class DCDC:
    ''' DCDC converter '''
    def __init__(self, beetle):
        self.beetle = beetle
        self.pin = gpiozero.OutputDevice(13, active_high=False)
        self.beetle.logger.info('DCDC poller initialized')

    def poll(self):
        # XXX for now just keep the dcdc on all the time when driving
        ac_present = self.beetle.gpio.get('ac_present')
        ignition = self.beetle.gpio.get('ignition')
        if ac_present == 0 and ignition == 1 and self.pin.value == 0:
            self.beetle.logger.info('turning on dcdc')
            self.pin.on()
        elif (ac_present == 1 or ignition == 0) and self.pin.value == 1:
            self.beetle.logger.info('turning off dcdc')
            self.pin.off()

class Gpio:
    ''' State class '''
    def __init__(self, beetle):
        self.beetle = beetle
        self.inputs = {}
        if beetle.location == 'back':
            self.inputs['ac_present'] = GpioInput(4, 'ac_present', beetle)
            self.inputs['ignition'] = GpioInput(24, 'ignition', beetle)
            self.inputs['charging'] = GpioInput(12, 'charging', beetle)
        self.beetle.logger.info('GPIO poller initialized')

    def get(self, name):
        if name in self.inputs:
            return self.inputs[name].pin.value
        else:
            return int(self.beetle.state.get(name))

    def poll(self):
        for name in self.inputs:
            new_value = self.inputs[name].pin.value
            # TODO: check if this gpio has a timeout in the state table
            if True: # new_value != self.inputs[name].prev_value:
                self.beetle.state.set(name, new_value)
                self.inputs[name].prev_value = new_value

class GpioInput:
    ''' GPIO input class '''
    def __init__(self, pin, name, beetle):
        self.pin = gpiozero.InputDevice(pin, pull_up=True)
        self.prev_value = self.pin.value
        beetle.state.set(name, self.prev_value)

class GPS:
    ''' GSP receiver class '''
    def __init__(self, beetle):
        self.beetle = beetle
        gpsd.connect()
        self.trip = float(self.beetle.state.get('trip_odometer'))
        self.charge = float(self.beetle.state.get('charge_odometer'))
        self.beetle.logger.info('GPS poller initialized')

    def poll(self):
        try:
            packet = gpsd.get_current()
            self.beetle.state.set('lat', '%.6f' % packet.lat)
            self.beetle.state.set('lon', '%.9f' % packet.lon)
            speed_str = '%.1f' % (packet.speed() * 2.237)
            self.beetle.state.set('speed', speed_str)
            new_position = packet.position()
            if self.beetle.gpio.get('ignition') == 1:
                d = distance(new_position, self.position).miles
                self.trip += d
                self.charge += d
                self.beetle.state.set('trip_odometer', '%.1f' % self.trip)
                self.beetle.state.set('charge_odometer', '%.1f' % self.charge)
            self.position = new_position
        except gpsd.NoFixError:
            self.beetle.logger.error('gps signal too low')

class PhoneHome:
    ''' Phone home to update remote status '''
    def __init__(self, beetle):
        self.beetle = beetle
        self.last_phone_home = 0.0

    def poll(self):
        now = time.time()
        delta = now - self.last_phone_home
        if delta < 300.0 and delta > 0.0:
            return
        self.last_phone_home = now
        self.beetle.cur.execute('SELECT * FROM state')
        rows = self.beetle.cur.fetchall()
        fname = 'state.txt'
        with open(fname, 'w+') as fout:
            for row in rows:
                fout.write('%s\t%s\t%s\t%.1f\n' % (row[1:5]))
            fout.flush()
            os.fsync(fout.fileno())
        cmd = ('scp -P 2222 %s pi@crystalpalace.ddns.net'
               ':/var/www/html/beetle/%s > /dev/null' % (fname, fname))
        subprocess.call(cmd, shell=True)

class State:
    ''' State class '''
    def __init__(self, beetle):
        self.beetle = beetle

    def get(self, name):
        now = datetime.now()
        self.beetle.cur.execute('SELECT * FROM state WHERE name = "%s";' % name)
        row = self.beetle.cur.fetchall()[0]
        ts = row[1]
        value = row[3]
        timeout = row[4]
        last_update = (now - ts).total_seconds()
        if timeout > 0.0 and (last_update > timeout or last_update < 0.0):
            self.beetle.logger.error('state variable %s last update was %.01f '
                                     'seconds ago' % (name, last_update))
            return None
        else:
            return value

    def set(self, name, value):
        self.beetle.cur.execute('UPDATE state SET ts = CURRENT_TIMESTAMP, '
                                'value = "%s" WHERE name = "%s";' % (value, name))
        self.beetle.db.commit()

class WiFi:
    ''' WiFi '''
    def __init__(self, beetle):
        self.beetle = beetle
        self.last_poll = 0.0
        self.prev_ac_present = 1
        self.beetle.logger.info('WiFi poller initialized')

    def poll(self):
        now = time.time()
        delta = now - self.last_poll
        if delta < 60.0 and delta > 0.0:
            return
        self.last_poll = now
        wifi = self.beetle.state.get('wifi')
        if 'wifi' == 'always':
            return
        # TODO: add mode to enable/disable wifi based on location
        # TODO: disable usb0 (phone home) connection when at home
        new_ac_present = self.beetle.gpio.get('ac_present')
        if new_ac_present == 1 and self.prev_ac_present == 0:
            if wifi != 'disabled':
                cmd = 'sudo ip link set up wlan0'
                subprocess.call(cmd, shell=True)
        elif new_ac_present == 0 and self.prev_ac_present == 1:
            if wifi != 'always':
                cmd = 'sudo ip link set down wlan0'
                subprocess.call(cmd, shell=True)
        self.prev_ac_present = new_ac_present

class Beetle:
    ''' Integration class for all the components of the car '''
    def __init__(self, location):
        self.location = location
        self.logger = setup_logger('beetle')
        self.db = setup_db(location)
        self.cur = self.db.cursor()
        self.state = State(self)
        self.pollers = []
        if location == 'back':
            ''' turn off dash light '''
            self.dash_light = gpiozero.OutputDevice(27, active_high=False)
            self.dash_light.on()
            ''' set up back-only pollers '''
            self.pollers.append(heating.BatteryHeater(self))
            self.pollers.append(DCDC(self))
            self.pollers.append(Charger(self))
        else: # self.location == 'front':
            ''' set up front-only pollers '''
            self.pollers.append(GPS(self))
            self.pollers.append(PhoneHome(self))
        ''' set up common pollers '''
        self.bms = bms.BatteryMonitoringSystem(self)
        self.pollers.append(self.bms)
        self.pollers.append(WiFi(self))
        self.gpio = Gpio(self)
        self.pollers.append(self.gpio)

    def poll(self):
        ''' Repeat tasks forever at desired frequences '''
        self.logger.info('starting pollers')
        prev_ts = time.time()
        while True:
            for poller in self.pollers:
                poller.poll()
            now = time.time()
            name = '%s_polling_period' % self.location
            period = '%.2f' % (now - prev_ts)
            self.state.set(name, period)
            prev_ts = now

if __name__== '__main__':

    ''' At boot, wait a minute for networking, mysql, etc. to start '''
    with open('/proc/uptime') as fin:
        uptime = float(fin.readline().split()[0])
        if uptime < 60.0:
            time.sleep(60.0 - uptime)

    '''
    The location of the pi determines what its responsibilities are.
    Extract it from the hostname which has the format 'beetle-<location>'
    '''
    location = socket.gethostname().split('-')[1]

    beetle = Beetle(location)
    beetle.poll()
