#!/usr/bin/env python3

import errno
import flask
import gpiozero
import gpsd
import json
import logging
import os
import requests
import smbus
import socket
import subprocess
import threading
import traceback
import time
import zmq

from geopy.distance import distance
from logging.handlers import RotatingFileHandler

import bms
import ds
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
        self.adjust = { 1 : (3.31, 1.0), 2 : (1.0, 0.0) }
        self.setup_and_start()
        self.beetle.logger.info('ADC poller initialized')

    def setup_and_start(self):
        try:
            nau.voltage_setup(self.bus, self.ch)
            nau.start_measurement(self.bus)
        except OSError:
            self.beetle.logger.error('Failed to set up and start measurement on ch. %d' % self.ch)

    def poll(self):
        try:
            v_nau = nau.get_voltage(self.bus)
        except OSError:
            self.beetle.logger.error('Failed to get ch. %d voltage' % self.ch)
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
        self.setup_and_start()

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

class ControllerFan:
    ''' Controller fan attached to controller heatsink '''
    def __init__(self, beetle):
        self.beetle = beetle
        self.pin = gpiozero.OutputDevice(19, active_high=False)
        self.beetle.state.set('controller_fan', 'disabled')
        self.last_poll = 0.0
        self.next_poll = 10
        self.beetle.logger.info('Controller fan poller initialized')

    def poll(self):
        now = time.time()
        delta = now - self.last_poll
        if delta < self.next_poll and delta > 0.0:
            return
        self.last_poll = now
        ''' get temperature '''
        try:
            c_temp = ds.get_temp('28-01143ba5cfaa')
        except IOError:
            self.beetle.logger.error('failed to read controller temperature')
            if self.pin.value == 1:
                self.beetle.logger.info('turning off controller fan (error)')
                self.pin.off()
                self.beetle.state.set('controller_fan', 'disabled')
            return
        self.beetle.state.set('controller_temp', '%.0f' % c_temp)
        ''' turn off when ignition is off or ac is present '''
        ignition = self.beetle.gpio.get('ignition')
        ac_present = self.beetle.gpio.get('ac_present')
        if ignition == 0 or ac_present == 1:
            if self.pin.value == 1:
                self.beetle.logger.info('turning off controller fan (no ignition, ac present)')
                self.pin.off()
                self.beetle.state.set('controller_fan', 'disabled')
            self.next_poll = 60
            return
        ''' check temperature and turn fan on/off '''
        if c_temp < 55.0:
            if self.pin.value == 1:
                self.beetle.logger.info('turning off controller fan (t=%.1f)' % c_temp)
                self.pin.off()
                self.beetle.state.set('controller_fan', 'disabled')
            self.next_poll = 10
            return
        if self.pin.value == 0:
            self.beetle.logger.info('turning on controller fan (t=%.1f)' % c_temp)
            self.pin.on()
            self.beetle.state.set('controller_fan', 'enabled')
            self.next_poll = 60

class DCDC:
    ''' DCDC converter '''
    def __init__(self, beetle):
        self.beetle = beetle
        self.pin = gpiozero.OutputDevice(13, active_high=False)
        self.beetle.state.set('dcdc', 'disabled')
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
            self.beetle.state.set(name, new_value)

class GpioInput:
    ''' GPIO input class '''
    def __init__(self, pin, name, beetle):
        self.pin = gpiozero.InputDevice(pin, pull_up=True)
        beetle.state.set(name, self.pin.value)

class GPS:
    ''' GSP receiver class '''
    def __init__(self, beetle):
        self.beetle = beetle
        try:
            subprocess.check_call('gpsctl --nmea /dev/ttyACM0', shell=True)
        except subprocess.CalledProcessError:
            self.beetle.logger.error('failed to set gps to nmea mode')
            pass
        gpsd.connect()
        self.position = None
        self.prev_ignition = self.beetle.state.get('ignition')
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
            ignition = self.beetle.state.get('ignition')
            if ignition and self.prev_ignition and int(ignition) == 1:
                if int(self.prev_ignition) == 0:
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

timeouts = {
    'ac_present' : 60,
    'ignition' : 60,
    'charging' : 60,
    'front_t_av' : 60,
    'back_t_av' : 60,
    'v' : 60,
    'v_av' : 60,
    'v_min' : 60,
    'v_max' : 60,
    'controller_temp' : 300,
    'v_acc_batt' : 60,
    'v_i_sense' : 60,
}

class State:
    ''' State class '''
    def __init__(self, beetle):
        self.beetle = beetle
        self.last_poll = 0.0
        self.heartbeat = int(time.time())

        # initialize from persistent store of state
        self.persistent_state_file = '/home/pi/state.json'
        try:
            with open(self.persistent_state_file) as fin:
                self.state = json.loads(fin.read())
        except FileNotFoundError:
            self.state = {}
            self.beetle.logger.error('state.json not found')

        # set up zmq pub/sub for keeping state in sync
        self.zmq_ctx = zmq.Context()
        self.pub_sock = self.zmq_ctx.socket(zmq.PUB)
        self.pub_sock.bind('tcp://*:5555')
        self.sub_sock = self.zmq_ctx.socket(zmq.SUB)
        self.sub_sock.connect('tcp://localhost:5555')
        if self.beetle.location == 'back':
            self.sub_sock.connect('tcp://10.10.10.1:5555')
        else:
            self.sub_sock.connect('tcp://10.10.10.2:5555')
        self.sub_sock.setsockopt_string(zmq.SUBSCRIBE, 'state')
        self.sub_thread = threading.Thread(target=self.sub_thread_func)
        self.sub_thread.daemon = True
        self.sub_thread.start()

        # start flask to serve state to webui
        self.rest_thread = threading.Thread(target=self.rest_thread_func)
        self.rest_thread.daemon = True
        self.rest_thread.start()

    def rest_thread_func(self):
        api = flask.Flask('state')

        log = logging.getLogger('werkzeug')
        log.setLevel(logging.ERROR)

        @api.route('/state', methods=['GET'])
        def state():
            return flask.jsonify(self.state)

        @api.route('/button', methods=['POST'])
        def button():
            button = flask.request.get_data().decode('utf-8')
            if button == 'reset':
                self.beetle.state.set('trip_odometer', '0.0')
            elif button in 'enable':
                self.beetle.state.set('charger', 'enabled')
            elif button == 'disable':
                self.beetle.state.set('charger', 'disabled')
            elif button == 'once':
                self.beetle.state.set('charger', 'once')
            else:
                self.beetle.logger.error('unexpected button %s' % button)
                return 'fail', 400
            return 'success', 200

        api.run(host='0.0.0.0')

    def sub_thread_func(self):
        while True:
            string = self.sub_sock.recv_string()
            topic, name, value = string.split()
            if topic != 'state':
                self.beetle.logger.error('unexpected zmq topic %s' % topic)
                continue
            if name == 'heartbeat':
                if value != self.beetle.location:
                    self.heartbeat = int(time.time())
                name = name + '_' + value
            self.state[name] = (value, int(time.time()))

    def poll(self):
        now = int(time.time())
        ''' check on threads '''
        if not self.sub_thread.is_alive():
            self.beetle.logger.error('state sub thread died')
            raise OSError
        if not self.rest_thread.is_alive():
            self.beetle.logger.error('state rest thread died')
            raise OSError
        ''' handle heartbeat and reconnect logic '''
        self.pub_sock.send_string('state heartbeat %s' % self.beetle.location)
        delta = now - self.heartbeat
        if delta > 30:
            if self.beetle.location == 'back':
                self.sub_sock.connect('tcp://10.10.10.1:5555')
            else:
                self.sub_sock.connect('tcp://10.10.10.2:5555')
        ''' update persistent state and phone home every 5 minutes '''
        delta = now - self.last_poll
        if delta < 300 and delta > 0:
            return
        self.last_poll = now
        self.write_persistent_state()
        if self.beetle.location == 'back':
            return
        ''' update usb0 ip in state table '''
        # TODO: find a cleaner way to get the usb0 ip address
        cmd = ['ip', 'addr', 'show', 'dev', 'usb0']
        try:
            output = subprocess.check_output(cmd)
            output = output.decode('utf-8')
            if 'inet 192.168.' in output:
                ip = output.split('inet 192.168.')[1].split('/')[0]
                self.beetle.state.set('ip', ip)
        except subprocess.CalledProcessError:
            pass
        ''' phone home '''
        # TODO: move this to a thread
        home_url = 'https://housejohns.com/beetle/rest/state'
        try:
            r = requests.post(home_url, json=self.state)
            if r.status_code != 200:
                self.beetle.logger.error('phone home got status '
                                         'code %d' % r.status_code)
        except OSError as e:
            if e.errno == errno.ENETUNREACH:
                self.beetle.logger.error('phone home failed due '
                                         'to unreachable network')
            elif e.errno == errno.ETIMEDOUT:
                self.beetle.logger.error('phone home failed due '
                                         'to network timeout')
            else:
                raise
        except requests.exceptions.ConnectionError:
            self.beetle.logger.error('phone home failed due to network fault')

    def write_persistent_state(self):
        with open(self.persistent_state_file, 'w+') as fout:
            fout.write(json.dumps(self.state, indent=4))
            fout.flush()
            os.fsync(fout.fileno())

    def get_json(self):
        return json.dumps(self.state, indent=4)

    def get(self, name):
        now = int(time.time())
        if name not in self.state:
            self.beetle.logger.error('state variable %s not found' % name)
            return None
        value, ts = self.state[name]
        timeout = 0
        if name in timeouts:
            timeout = timeouts[name]
        last_update = now - ts
        if timeout > 0 and (last_update > timeout or last_update < -5):
            self.beetle.logger.error('state variable %s last update was %d '
                                     'seconds ago' % (name, last_update))
            return None
        else:
            return value

    def set(self, name, value):
        self.pub_sock.send_string('state %s %s' % (name, value))

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
        output = subprocess.check_output(cmd, shell=True)
        output = output.decode('utf-8')
        up = 'state UP' in output
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
        self.pollers = []
        ''' set up common pollers '''
        self.state = State(self)
        self.pollers.append(self.state)
        self.bms = bms.BatteryMonitoringSystem(self)
        self.pollers.append(self.bms)
        self.gpio = Gpio(self)
        self.pollers.append(self.gpio)
        # ~ self.pollers.append(WiFi(self))
        if location == 'back':
            ''' turn off dash light '''
            self.dash_light = gpiozero.OutputDevice(27, active_high=False)
            self.dash_light.on()
            ''' set up back-only pollers '''
            self.pollers.append(heating.BatteryHeater(self))
            self.pollers.append(ADC(self))
            self.pollers.append(ControllerFan(self))
            self.pollers.append(DCDC(self))
            self.pollers.append(Charger(self))
        else:
            ''' set up front-only pollers '''
            self.pollers.append(GPS(self))

    def poll(self):
        ''' Repeat tasks forever at desired frequences '''
        self.logger.info('starting pollers')
        prev_ts = time.time()
        try:
            while True:
                for poller in self.pollers:
                    poller.poll()
                now = time.time()
                name = '%s_polling_period' % self.location
                period = '%.2f' % (now - prev_ts)
                self.state.set(name, period)
                prev_ts = now
        except BaseException as e:
            self.logger.error(traceback.format_exc())
            self.state.write_persistent_state()
            raise

if __name__== '__main__':

    ''' At boot, wait a minute for networking, etc. to start '''
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
