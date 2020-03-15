#!/usr/bin/env python

import gpiozero
import MySQLdb
import smbus
import socket

from datetime import datetime

import batteries

LOG = open('charge.log', 'a+', buffering=1)

def log_print(str):
    ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print '%s %s' % (ts, str)
    LOG.write('%s %s\n' % (ts, str))

def main():

    # Setup EVCC loop control if we're running on the back pi
    location = socket.gethostname().split('-')[1]
    if location == 'back':
        evcc = gpiozero.OutputDevice(6, active_high=False)
        evcc.on()
        host = 'localhost'
    else:
        host = '10.10.10.2'

    # Setup db connection
    with open('db_passwd.txt') as fin:
        passwd = fin.read()
    db = MySQLdb.connect(host=host, user='beetle', passwd=passwd, db='beetle')
    cur = db.cursor()

    # Setup BMS
    err_str = None
    bus = smbus.SMBus(1)
    batts = batteries.Batteries(bus)
    t_av_av_list = []
    while True:
        t_av_list = []
        batts.do_measurements()
        print ''
        for batt in batts.battery_iter():
            g = batt.get_group()
            t = batt.get_last_temperature()
            t_av = batt.get_average_temperature()
            t_av_list.append(t_av)
            v = batt.get_last_voltage()
            v_av = batt.get_average_voltage()
            id_str = 'Group %2d: t=%.01f (%.01f) v=%.03f (%.03f)' % (g, t, t_av, v, v_av)
            log_print(id_str)
            cur.execute('INSERT INTO bms (cell_group, voltage, temperature) '
                        'VALUES (%d, %.03f, %.01f);' % (g, v, t))
            #~ if err_str or t_av > 50.0 or v_av > 8.1 or v_av < 6.0:
                #~ if not err_str:
                    #~ evcc.off()
                    #~ err_str = id_str
                #~ log_print('ERROR: disabled EVCC because of %s' % err_str)
        db.commit()
        t_av_av = sum(t_av_list) / float(len(t_av_list))
        t_av_av_list.append(t_av_av)
        if len(t_av_av_list) > 10:
            t_av_av_list.pop(0)
        t_av_av_av = sum(t_av_av_list) / float(len(t_av_av_list))
        log_print('t_av %0.1f' % t_av_av_av)

if __name__== '__main__':
    main()
