#!/usr/bin/env python

import gpiozero
import gpsd
import logging
import MySQLdb
import os
import smbus
import socket
import subprocess
import time

from datetime import datetime
from geopy.distance import distance
from logging.handlers import RotatingFileHandler

import bms
import heating
import nau

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

def at_home(lat, lon):
    '''
    west bound: -93.3555
    east bound: -93.3545
    north bound: 45.0180
    south bound: 45.0167
    '''
    if lat < 45.0180 and lat > 45.0167 and lon < -93.3545 and lon > -93.3555:
        return True
    return False

class ADC:
    ''' ADC that measures 12V battery voltage and current sensor output '''
    def __init__(self, beetle):
        self.beetle = beetle
        self.bus = smbus.SMBus(0)
        nau.chip_setup(self.bus)
        self.ch = 1
        self.count = { 1 : 5, 2 : 3 }
        self.values = { 1 : [], 2 : [] }
        self.adjust = { 1 : (3.31, -0.0391), 2 : (1.0, 0.0) }
        nau.voltage_setup(self.bus, self.ch)
        nau.start_measurement(self.bus)
        self.beetle.logger.info('ADC poller initialized')

    def poll(self):
        v_nau = nau.get_voltage(self.bus)
        scale, offset = self.adjust[self.ch]
        v = v_nau * scale + offset
        self.values[self.ch].append(v)
        if len(self.values[self.ch]) > self.count[self.ch]:
            self.values[self.ch].pop(0)
        v_av = sum(self.values[self.ch]) / len(self.values[self.ch])
        if self.ch == 1:
            ''' Ch. 1 is 12V battery '''
            self.beetle.state.set('v_acc_batt', '%.2f' % v_av)
            self.ch = 2
        else:
            ''' Ch. 2 is current sensor '''
            self.beetle.state.set('v_i_sense', '%.3f' % v_av)
            self.ch = 1
        nau.voltage_setup(self.bus, self.ch)
        nau.start_measurement(self.bus)

class Charger:
    ''' Charger '''
    def __init__(self, beetle):
        self.beetle = beetle
        self.pin = gpiozero.OutputDevice(5, active_high=False)
        self.last_poll = time.time()
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
        self.last_poll = 0.0
        self.next_poll = 5
        self.beetle.logger.info('DCDC poller initialized')

    def poll(self):
        now = time.time()
        delta = now - self.last_poll
        if delta < self.next_poll and delta > 0.0:
            return
        self.last_poll = now
        ''' never turn on dcdc when ac is present'''
        if self.beetle.gpio.get('ac_present') == 1:
            if self.pin.value == 1:
                self.beetle.logger.info('turning off dcdc (ac present)')
                self.pin.off()
                self.beetle.state.set('dcdc', 'disabled')
            self.next_poll = 60
            return
        ''' on at 12V for at least 1 minute, off at 12.5V '''
        v_acc = float(self.beetle.state.get('v_acc_batt'))
        if v_acc < 12.0 and self.pin.value == 0:
            self.beetle.logger.info('turning on dcdc')
            self.pin.on()
            self.beetle.state.set('dcdc', 'enabled')
            self.next_poll = 60
        elif v_acc > 12.5 and self.pin.value == 1:
            self.beetle.logger.info('turning off dcdc')
            self.pin.off()
            self.beetle.state.set('dcdc', 'disabled')
            self.next_poll = 5

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
        self.position = None
        self.prev_ignition = self.beetle.gpio.get('ignition')
        self.trip = float(self.beetle.state.get('trip_odometer'))
        self.charge = float(self.beetle.state.get('charge_odometer'))
        self.beetle.logger.info('GPS poller initialized')

    def poll(self):
        try:
            packet = gpsd.get_current()
            self.beetle.state.set('lat', '%.6f' % packet.lat)
            self.beetle.state.set('lon', '%.9f' % packet.lon)
            speed_str = '%.0f' % (packet.speed() * 2.237)
            self.beetle.state.set('speed', speed_str)
            new_position = packet.position()
            ignition = self.beetle.gpio.get('ignition')
            if ignition == 1:
                if self.prev_ignition == 0:
                    self.trip = float(self.beetle.state.get('trip_odometer'))
                    self.charge = float(self.beetle.state.get('charge_odometer'))
                if self.position != None:
                    d = distance(new_position, self.position).miles
                    self.trip += d
                    self.charge += d
                    self.beetle.state.set('trip_odometer', '%.1f' % self.trip)
                    self.beetle.state.set('charge_odometer', '%.1f' % self.charge)
            self.prev_ignition = ignition
            self.position = new_position
        except gpsd.NoFixError:
            self.beetle.logger.error('gps signal too low')

class PhoneHome:
    '''
    Phone home to update remote status

    TODO: Down usb0 and phone home through wifi when at home. This requires
    figuring out how to programatically enable usb tethering on the Nexus 5
    since it times out and disables itself when there is no traffic.
    '''
    def __init__(self, beetle):
        self.beetle = beetle
        self.last_phone_home = 0.0
        self.proc = None
        self.beetle.logger.info('PhoneHome poller initialized')

    def poll(self):
        ''' Update usb0 ip in state table '''
        cmd = 'ip addr show dev usb0'
        try:
            output = subprocess.check_output(cmd, shell=True)
            if 'inet 192.168.' in output:
                ip = output.split('inet 192.168.')[1].split('/')[0]
                self.beetle.state.set('ip', ip)
        except CalledProcessError:
            pass
        ''' Update local file as often as possible for webui '''
        self.beetle.cur.execute('SELECT * FROM state')
        rows = self.beetle.cur.fetchall()
        json_rows = []
        for row in rows:
            ts = row[1]
            name = row[2]
            value = row[3]
            timeout = row[4]
            json_rows.append('"%s":{"value":"%s","ts":"%s","timeout":"%s"}' %
                             (name, value, ts, timeout))
        json = '{%s}' % ','.join(json_rows)
        fname = 'state.json'
        write_path = '/var/www/html/%s' % fname
        with open(write_path, 'w+') as fout:
            fout.write(json)
            fout.flush()
            os.fsync(fout.fileno())
        ''' Only send the data home every 5 minutes '''
        now = time.time()
        delta = now - self.last_phone_home
        if delta < 300.0 and delta > 0.0:
            return
        if self.proc != None and self.proc.poll() == None:
            self.proc.kill()
        self.last_phone_home = now
        cmd = ('scp -P 2222 %s pi@crystalpalace.ddns.net'
               ':/var/www/html/beetle/%s > /dev/null' % (write_path, fname))
        self.proc = subprocess.Popen(cmd, shell=True)

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
        if timeout > 0.0 and (last_update > timeout or last_update < -5.0):
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
        self.beetle.logger.info('WiFi poller initialized')

    def poll(self):
        now = time.time()
        delta = now - self.last_poll
        if delta < 60.0 and delta > 0.0:
            return
        self.last_poll = now
        ''' get current setting and state '''
        mode = self.beetle.state.get('wifi')
        lat = self.beetle.state.get('lat')
        lon = self.beetle.state.get('lon')
        ac_present = self.beetle.gpio.get('ac_present')
        cmd = 'ip link show dev wlan0'
        up = 'state UP' in subprocess.check_output(cmd, shell=True)
        ''' determine if wlan0 state needs to change '''
        action = None
        if mode == 'disabled':
            if up:
                action = 'down'
        elif mode == 'on_ac':
            if not up and ac_present == 1:
                action = 'up'
        elif mode == 'at_home':
            if not up and at_home(lat, lon):
                action = 'up'
        else: # mode == 'always':
            if not up:
                action = 'up'
        ''' change wlan0 state if necessary '''
        if action == None:
            return
        cmd = 'sudo ip link set %s wlan0' % action
        subprocess.call(cmd, shell=True)
        self.beetle.logger.info('wlan0 %s' % action)

class Beetle:
    ''' Integration class for all the components of the car '''
    def __init__(self, location):
        self.location = location
        self.logger = setup_logger('beetle')
        self.db = setup_db(location)
        self.cur = self.db.cursor()
        self.state = State(self)
        self.pollers = []
        ''' set up common pollers '''
        self.bms = bms.BatteryMonitoringSystem(self)
        self.pollers.append(self.bms)
        self.gpio = Gpio(self)
        self.pollers.append(self.gpio)
        self.pollers.append(WiFi(self))
        if location == 'back':
            ''' turn off dash light '''
            self.dash_light = gpiozero.OutputDevice(27, active_high=False)
            self.dash_light.on()
            ''' set up back-only pollers '''
            self.pollers.append(heating.BatteryHeater(self))
            self.pollers.append(ADC(self))
            self.pollers.append(DCDC(self))
            self.pollers.append(Charger(self))
        else:
            ''' set up front-only pollers '''
            self.pollers.append(GPS(self))
            self.pollers.append(PhoneHome(self))

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
