'''
Battery Monitoring System (BMS)
'''

import gpiozero
import smbus
import time

from datetime import datetime

import batteries

HOLDOFF = 15.0 # wait this long for data to accumulate before doing anything

class BatteryMonitoringSystem:
    ''' BMS class '''
    def __init__(self, beetle):
        self.beetle = beetle
        self.init_time = time.time()
        self.last_poll = self.init_time
        self.last_history = self.init_time - 3600.0 + HOLDOFF
        self.bus = smbus.SMBus(1)
        self.batts = batteries.Batteries(self.bus, self.beetle.location)
        if self.beetle.location == 'back':
            self.loop = gpiozero.OutputDevice(6, active_high=False)
        ''' values passed from process() to history() '''
        self.front_t_av = 0.0
        self.back_t_av = 0.0
        self.v = 0.0
        self.v_av = 0.0
        self.v_min = 0.0
        self.v_max = 0.0
        self.beetle.logger.info('BMS poller initialized')

    def poll(self):
        self.gather()
        self.last_poll = time.time()
        if self.beetle.location == 'back':
            self.process()
            ''' record history at a variable rate '''
            period = 3600.0
            if self.beetle.gpio.get('ignition') == 1:
                period = 0.0
            elif self.beetle.gpio.get('charging') == 1:
                period = 60.0
            elif self.beetle.gpio.get('ac_present') == 0:
                period = 300.0
            delta = self.last_poll - self.last_history
            if delta > period or delta < 0.0:
                self.last_history = self.last_poll
                self.history()

    def gather(self):
        try:
            self.batts.do_measurements()
        except OSError:
            self.beetle.logger.error('measurement(s) failed')
        else:
            for batt in self.batts.battery_iter():
                g = batt.get_group()
                t = batt.get_last_temperature()
                t_av = batt.get_average_temperature()
                v = batt.get_last_voltage()
                v_av = batt.get_average_voltage()
                self.beetle.cur.execute('UPDATE bms SET ts = CURRENT_TIMESTAMP, '
                                        't = %.01f, t_av = %.01f, v = %.03f, '
                                        'v_av = %.03f WHERE cg = %d;' %
                                        (t, t_av, v, v_av, g))
            self.beetle.db.commit()

    def process(self):
        if time.time() - self.init_time < HOLDOFF:
            return
        self.beetle.cur.execute('SELECT cg, ts, t, t_av, v, v_av FROM bms')
        rows = self.beetle.cur.fetchall()
        errors = 0
        now = datetime.now()
        if len(rows) < 15:
            self.beetle.logger.error('missing cell group(s)')
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
            # determine the temperature threshold
            ac_present = self.beetle.gpio.get('ac_present')
            if ac_present == 1:
                t_thresh = 55.0
            else:
                t_thresh = 60.0
            if t_av < 0.0 or t_av > t_thresh:
                self.beetle.logger.error('group %d t_av=%.01f' % (cg, t_av))
                errors += 1
            # allow less than 6 volts if AC present (for charging)
            if v_av >= 8.1 or (v_av < 6.0 and ac_present == 0):
                self.beetle.logger.error('group %d v_av=%.03f' % (cg, v_av))
                errors += 1
            last_measurements = (now - ts).total_seconds()
            if last_measurements > 60.0 or last_measurements < 0.0:
                self.beetle.logger.error('group %d last measurements were %.01f '
                                         'seconds ago' % (cg, last_measurements))
                errors += 1
            if cg < 9:
                front_t_arr.append(t)
            else:
                back_t_arr.append(t)
            v_arr.append(v)
        if errors > 0 and self.loop.value == 1:
            self.beetle.logger.error('disabling evcc loop due to error(s)')
            self.loop.off()
        elif errors == 0 and self.loop.value == 0:
            self.beetle.logger.info('enabling evcc loop')
            self.loop.on()
        if len(front_t_arr) > 0:
            self.front_t_av = sum(front_t_arr) / float(len(front_t_arr))
        else:
            self.front_t_av = 0.0
        if len(back_t_arr) > 0:
            self.back_t_av = sum(back_t_arr) / float(len(back_t_arr))
        else:
            self.back_t_av = 0.0
        self.v_av = sum(v_arr) / float(len(v_arr))
        self.v = sum(v_arr)
        self.v_min = min(v_arr)
        self.v_max = max(v_arr)
        self.beetle.state.set('front_t_av', '%.0f' % self.front_t_av)
        self.beetle.state.set('back_t_av', '%.0f' % self.back_t_av)
        self.beetle.state.set('v', '%.01f' % self.v)
        self.beetle.state.set('v_av', '%.02f' % self.v_av)
        self.beetle.state.set('v_min', '%.02f' % self.v_min)
        self.beetle.state.set('v_max', '%.02f' % self.v_max)

    def history(self):
        amps = float(self.beetle.state.get('amps'))
        charge_wh = float(self.beetle.state.get('charge_wh'))
        speed = float(self.beetle.state.get('speed'))
        lat = float(self.beetle.state.get('lat'))
        lon = float(self.beetle.state.get('lon'))
        sql = ('INSERT INTO history (front_t_av, back_t_av, v, v_av, v_min, '
               'v_max, amps, charge_wh, speed, lat, lon) VALUES (%.1f, %.1f, '
               '%.1f, %.3f, %.3f, %.3f, %.1f, %.1f, %.1f, %.6f, %.9f);' %
               (self.front_t_av, self.back_t_av, self.v, self.v_av, self.v_min,
                self.v_max, amps, charge_wh, speed, lat, lon))
        self.beetle.cur.execute(sql)
        self.beetle.db.commit()
