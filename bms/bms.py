#!/usr/bin/env python

import gpiozero
import MySQLdb
import smbus
import socket
import sys

from datetime import datetime

import batteries

HOLDOFF = 15.0 # wait this long for data to accumulate before doing anything

class BatteryMonitoringSystem:
    ''' BMS class '''
    def __init__(self, logger, cur):
        self.logger = logger
        self.cur = cur
        self.loop = gpiozero.OutputDevice(6, active_high=False)
        self.rows = None
        self.init_time = datetime.now()

    def gather(self):
        if (datetime.now() - self.init_time).total_seconds() < HOLDOFF:
            return
        self.cur.execute('SELECT a.cg, a.ts, a.t_av, a.v_av FROM ( '
                         'SELECT b.*, ROW_NUMBER() OVER (PARTITION BY cell_group ORDER BY id DESC) AS rn '
                         'FROM bms AS b ) AS a WHERE rn = 1')
        self.rows = cur.fetchall()

    def process(self):
        if self.rows == None:
            return
        errors = 0
        now = datetime.now()
        if len(self.rows) < 15:
            self.logger.error('missing cell group(s)')
            errors += 1
        for row in self.rows:
            cg = row[0]
            ts = row[1]
            t_av = row[2]
            v_av = row[3]
            if t_av < 0.0 or t_av > 50.0:
                self.logger.error('group %d t_av=%.01f' % (cg, t_av))
                errors += 1
            # TODO: allow less than 6 volts if AC present (for charging)
            if v_av >= 8.1 or v_av < 6.0:
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

    # ~ def cleanup(self):
        # TODO: average the results into the history table

def poll(location, logger, cur):
    bus = smbus.SMBus(1)
    batts = batteries.Batteries(bus, location)
    while True:
        try:
            batts.do_measurements()
        except OSError:
            logger.error('measurement(s) failed')
            break
        for batt in batts.battery_iter():
            g = batt.get_group()
            t = batt.get_last_temperature()
            t_av = batt.get_average_temperature()
            v = batt.get_last_voltage()
            v_av = batt.get_average_voltage()
            cur.execute('INSERT INTO bms (cell_group, t, t_av, v, v_av) '
                        'VALUES (%d, %.01f, %.01f, %.03f, %.03f);' % (g, t, t_av, v, v_av))
        db.commit()

# ~ LOG = open('charge.log', 'a+', buffering=1)

# ~ def log_print(str):
    # ~ ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    # ~ print '%s %s' % (ts, str)
    # ~ LOG.write('%s %s\n' % (ts, str))

# ~ ON_TEMP = 17.5
# ~ OFF_TEMP = 18.0

# ~ def heat_control(front_av, back_av, front_heat, back_heat):
    # ~ if front_temp <= ON_TEMP:
        # ~ if front_heat.value == 0:
            # ~ front_heat.on()
            # ~ log_print('front on')
    # ~ elif front_temp >= OFF_TEMP:
        # ~ if front_heat.value == 1:
            # ~ front_heat.off()
            # ~ log_print('front off')
    # ~ if back_temp <= ON_TEMP:
        # ~ if back_heat.value == 0:
            # ~ back_heat.on()
            # ~ log_print('back on')
    # ~ elif back_temp >= OFF_TEMP:
        # ~ if back_heat.value == 1:
            # ~ back_heat.off()
            # ~ log_print('back off')

# ~ def back_actions(cur, evcc, front_heat, back_heat):
    # ~ cur.execute('SELECT a.cg, a.ts, a.t_av, a.v_av FROM ( '
                # ~ 'SELECT b.*, ROW_NUMBER() OVER (PARTITION BY cell_group ORDER BY id DESC) AS rn '
                # ~ 'FROM bms AS b ) AS a WHERE rn = 1')
    # ~ now = datetime.now()
    # ~ rows = cur.fetchall()
    # ~ errors = 0
    # ~ t_av_front = []
    # ~ t_av_back = []
    # ~ if len(rows) < 15:
        # ~ log_print('missing cell group(s)')
        # ~ errors += 1
    # ~ for row in rows:
        # ~ g = row[0]
        # ~ ts = row[1]
        # ~ t_av = row[2]
        # ~ v_av = row[3]
        # ~ if t_av < 0.0 or t_av > 50.0:
            # ~ log_print('group %d t_av=%.01f' % (group, t_av))
            # ~ errors += 1
        # ~ if v_av >= 8.1 or v_av < 6.0:
            # ~ log_print('group %d v_av=%.03f' % (group, v_av))
            # ~ errors += 1
        # ~ last_measurements = (now - ts).total_seconds()
        # ~ if last_measurements > 60.0 or last_measurements < 0.0:
            # ~ log_print('group %d last measurements were %.01f seconds ago' % (group, last_measurements))
            # ~ errors += 1
        # ~ if g < 9:
            # ~ t_av_front.append(t_av)
        # ~ else:
            # ~ t_av_back.append(t_av)
    # ~ if errors > 0 and evcc.value == 1:
        # ~ log_print('disabling evcc due to error(s)')
        # ~ evcc.off()
        # ~ sys.exit(1)
    # ~ t_av_av_front = sum(t_av_front) / float(len(t_av_front))
    # ~ t_av_av_back = sum(t_av_back) / float(len(t_av_back))
    # ~ heat_control(t_av_av_front, t_av_av_back, front_heat, back_heat)

# ~ def main():

    # ~ # Setup EVCC loop control if we're running on the back pi
    # ~ location = socket.gethostname().split('-')[1]
    # ~ if location == 'back':
        # ~ evcc = gpiozero.OutputDevice(6, active_high=False)
        # ~ evcc.on()
        # ~ front_heat = gpiozero.OutputDevice(22, active_high=False)
        # ~ back_heat = gpiozero.OutputDevice(23, active_high=False)
        # ~ host = 'localhost'
    # ~ else:
        # ~ host = '10.10.10.2'

    # ~ # Setup db connection
    # ~ with open('db_passwd.txt') as fin:
        # ~ passwd = fin.read()
    # ~ db = MySQLdb.connect(host=host, user='beetle', passwd=passwd, db='beetle')
    # ~ cur = db.cursor()

    # ~ # Setup BMS
    # ~ err_str = None
    # ~ bus = smbus.SMBus(1)
    # ~ batts = batteries.Batteries(bus, location)
    # ~ t_av_av_list = []
    # ~ holdoff = 5
    # ~ while True:
        # ~ t_av_list = []
        # ~ print ''
        # ~ try:
            # ~ batts.do_measurements()
        # ~ except OSError:
            # ~ if location == 'back':
                # ~ evcc.off()
                # ~ log_print('disabling evcc due to measurement error(s)')
            # ~ log_print('exiting due to measurement error(s)')
            # ~ sys.exit(1)
        # ~ for batt in batts.battery_iter():
            # ~ g = batt.get_group()
            # ~ t = batt.get_last_temperature()
            # ~ t_av = batt.get_average_temperature()
            # ~ t_av_list.append(t_av)
            # ~ v = batt.get_last_voltage()
            # ~ v_av = batt.get_average_voltage()
            # ~ id_str = 'Group %2d: t=%.01f (%.01f) v=%.03f (%.03f)' % (g, t, t_av, v, v_av)
            # ~ log_print(id_str)
            # ~ cur.execute('INSERT INTO bms (cell_group, t, t_av, v, v_av) '
                        # ~ 'VALUES (%d, %.01f, %.01f, %.03f, %.03f);' % (g, t, t_av, v, v_av))
        # ~ db.commit()

        # ~ t_av_av = sum(t_av_list) / float(len(t_av_list))
        # ~ t_av_av_list.append(t_av_av)
        # ~ if len(t_av_av_list) > 10:
            # ~ t_av_av_list.pop(0)
        # ~ t_av_av_av = sum(t_av_av_list) / float(len(t_av_av_list))
        # ~ log_print('t_av %0.1f' % t_av_av_av)

        # ~ if location == 'back' and holdoff == 0:
            # ~ back_actions(cur, evcc, front_heat, back_heat)
        # ~ else:
            # ~ holdoff -= 1

# ~ if __name__== '__main__':
    # ~ main()
