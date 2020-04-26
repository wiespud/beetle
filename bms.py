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
from datetime import timedelta

import batteries

HOLDOFF = 15.0 # wait this long for data to accumulate before doing anything

class BatteryMonitoringSystem:
    ''' BMS class '''
    def __init__(self, beetle, logger, db, location):
        self.beetle = beetle
        self.logger = logger
        self.db = db
        self.cur = db.cursor()
        self.location = location
        self.init_time = datetime.now()
        self.bus = smbus.SMBus(1)
        self.batts = batteries.Batteries(self.bus, location)
        if location == 'back':
            self.loop = gpiozero.OutputDevice(6, active_high=False)

    def as_often_as_possible(self):
        ''' Do these tasks as often as possible '''
        self.gather()
        if self.location == 'back':
            self.process()

    def every_minute(self):
        ''' Do these tasks once a minute '''
        self.cleanup()

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
                self.cur.execute('INSERT INTO bms (cg, t, t_av, v, v_av) '
                                 'VALUES (%d, %.01f, %.01f, %.03f, %.03f);' % (g, t, t_av, v, v_av))
            self.db.commit()

    def process(self):
        if (datetime.now() - self.init_time).total_seconds() < HOLDOFF:
            return
        self.cur.execute('SELECT a.cg, a.ts, a.t_av, a.v_av FROM ( '
                         'SELECT b.*, ROW_NUMBER() OVER (PARTITION BY cg ORDER BY id DESC) AS rn '
                         'FROM bms AS b ) AS a WHERE rn = 1')
        rows = self.cur.fetchall()
        errors = 0
        now = datetime.now()
        if len(rows) < 15:
            self.logger.error('missing cell group(s)')
            errors += 1
        for row in rows:
            cg = row[0]
            ts = row[1]
            t_av = row[2]
            v_av = row[3]
            if t_av < 0.0 or t_av > 50.0:
                self.logger.error('group %d t_av=%.01f' % (cg, t_av))
                errors += 1
            # TODO: allow less than 6 volts if AC present (for charging)
            if v_av >= 8.1 or (v_av < 6.0 and self.beetle.ac_present.value == 0):
                self.logger.error('group %d v_av=%.03f' % (cg, v_av))
                errors += 1
            last_measurements = (now - ts).total_seconds()
            if last_measurements > 60.0 or last_measurements < 0.0:
                self.logger.error('group %d last measurements were %.01f seconds ago' % (cg, last_measurements))
                errors += 1
        if errors > 0 and self.loop.value == 1:
            self.logger.error('disabling evcc loop due to error(s)')
            self.loop.off()
        elif errors == 0 and self.loop.value == 0:
            self.logger.info('enabling evcc loop')
            self.loop.on()

    def cleanup(self):
        self.cur.execute('SELECT MIN(ts), MAX(ts) FROM bms')
        rows = self.cur.fetchall()
        min_ts = rows[0][0]
        max_ts = rows[0][1]
        if min_ts == None or max_ts == None:
            return
        if min_ts.minute == max_ts.minute:
            return
        match_ts = datetime(min_ts.year, min_ts.month, min_ts.day, min_ts.hour, min_ts.minute, 0)
        while (max_ts - match_ts).total_seconds() > 60.0:
            match_ts_str = '%s' % match_ts
            match_ts_str = match_ts_str[:-3]
            front_t_arr = []
            back_t_arr = []
            v_arr = []
            self.cur.execute('SELECT cg, AVG(t), AVG(v) FROM bms '
                             'WHERE ts LIKE \'%s%%\' GROUP BY cg' % match_ts_str)
            rows = self.cur.fetchall()
            if len(rows) > 0:
                for row in rows:
                    cg = row[0]
                    t = row[1]
                    v = row[2]
                    if cg < 9:
                        front_t_arr.append(t)
                    else:
                        back_t_arr.append(t)
                    v_arr.append(v)
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
                                 'VALUES (%.01f, %.01f, %.03f, %.03f, %.03f, %.03f);' % (front_t_av,
                                 back_t_av, v, v_av, v_min, v_max))
                self.cur.execute('DELETE FROM bms WHERE ts LIKE \'%s%%\'' % match_ts_str)
            match_ts += timedelta(0, 60)
        self.db.commit()
