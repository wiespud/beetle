#!/usr/bin/env python

import datetime
import MySQLdb
import time

with open('db_passwd.txt') as fin:
    passwd = fin.read()
db = MySQLdb.connect(host='localhost', user='beetle', passwd=passwd, db='beetle')
cur = db.cursor()

while True:
    cur.execute('SELECT cg, v, v_av FROM bms')
    rows = cur.fetchall()
    print datetime.datetime.now()
    print 'cg v     v_av'
    for row in rows:
        cg = row[0]
        v = row[1]
        v_av = row[2]
        if float(v_av) < 6.3:
            print '%2s %-5s %-5s done!\a' % (cg, v, v_av)
        elif float(v_av) < 6.32:
            print '%2s %-5s %-5s getting close' % (cg, v, v_av)
        else:
            print '%2s %-5s %-5s' % (cg, v, v_av)
    print ''
    time.sleep(5)
    db.commit()

