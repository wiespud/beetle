'''
Battery Monitoring System (BMS)
'''

import gpiozero
import MySQLdb
import smbus
import socket
import sys
import time

from datetime import datetime

import batteries

HOLDOFF = 15.0 # wait this long for data to accumulate before doing anything

class BatteryMonitoringSystem:
    ''' BMS class '''
    def __init__(self, beetle):
        self.beetle = beetle
        self.logger = beetle.logger
        self.db = beetle.db
        self.cur = self.db.cursor()
        self.location = beetle.location
        self.init_time = datetime.now()
        self.bus = smbus.SMBus(1)
        self.batts = batteries.Batteries(self.bus, self.location)
        if self.location == 'back':
            self.loop = gpiozero.OutputDevice(6, active_high=False)

    def as_often_as_possible(self):
        ''' Do these tasks as often as possible '''
        self.gather()
        if self.location == 'back' and (self.beetle.ignition.value == 1 or
                                        self.beetle.charging.value == 1):
            self.process()

    def every_minute(self):
        ''' Do these tasks once a minute '''
        if self.beetle.ignition.value == 0 and self.beetle.charging.value == 0:
            self.process()

    def gather(self):
        try:
            self.batts.do_measurements()
        except OSError:
            self.logger.error('measurement(s) failed')
        else:
            for batt in self.batts.battery_iter():
                g = batt.get_group()
                t = batt.get_last_temperature()
                t_av = batt.get_average_temperature()
                v = batt.get_last_voltage()
                v_av = batt.get_average_voltage()
                self.cur.execute('UPDATE bms SET ts = CURRENT_TIMESTAMP, '
                                 't = %.01f, t_av = %.01f, v = %.03f, v_av = %.03f '
                                 'WHERE cg = %d;' % (t, t_av, v, v_av, g))
            self.db.commit()

    def process(self):
        if (datetime.now() - self.init_time).total_seconds() < HOLDOFF:
            return
        self.cur.execute('SELECT cg, ts, t, t_av, v, v_av FROM bms')
        rows = self.cur.fetchall()
        errors = 0
        now = datetime.now()
        if len(rows) < 15:
            self.logger.error('missing cell group(s)')
            errors += 1
        front_t_arr = []
        back_t_arr = []
        v_arr = []
        for row in rows:
            cg = row[0]
            ts = row[1]
            t = row[2]
            t_av = row[3]
            v = row[4]
            v_av = row[5]
            if t_av < 0.0 or t_av > 50.0:
                self.logger.error('group %d t_av=%.01f' % (cg, t_av))
                errors += 1
            # allow less than 6 volts if AC present (for charging)
            if v_av >= 8.1 or (v_av < 6.0 and self.beetle.ac_present.value == 0):
                self.logger.error('group %d v_av=%.03f' % (cg, v_av))
                errors += 1
            last_measurements = (now - ts).total_seconds()
            if last_measurements > 60.0 or last_measurements < 0.0:
                self.logger.error('group %d last measurements were %.01f seconds ago' % (cg, last_measurements))
                errors += 1
            if cg < 9:
                front_t_arr.append(t)
            else:
                back_t_arr.append(t)
            v_arr.append(v)
        if errors > 0 and self.loop.value == 1:
            self.logger.error('disabling evcc loop due to error(s)')
            self.loop.off()
        elif errors == 0 and self.loop.value == 0:
            self.logger.info('enabling evcc loop')
            self.loop.on()
        if len(front_t_arr) > 0:
            front_t_av = sum(front_t_arr) / float(len(front_t_arr))
        else:
            front_t_av = 0.0
        if len(back_t_arr) > 0:
            back_t_av = sum(back_t_arr) / float(len(back_t_arr))
        else:
            back_t_av = 0.0
        v_av = sum(v_arr) / float(len(v_arr))
        v = sum(v_arr)
        v_min = min(v_arr)
        v_max = max(v_arr)
        self.cur.execute('INSERT INTO history (front_t_av, back_t_av, v, v_av, v_min, v_max) '
                         'VALUES (%.01f, %.01f, %.03f, %.03f, %.03f, %.03f);' %
                         (front_t_av, back_t_av, v, v_av, v_min, v_max))
        self.db.commit()
