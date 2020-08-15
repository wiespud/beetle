'''
Interface to GPS receiver

https://github.com/MartijnBraam/gpsd-py3/blob/master/DOCS.md
'''

import gpsd
import os
import subprocess
import time

HSPEED_FILE = '/var/www/html/hspeed.txt'
FSPEED_FILE = '/var/www/html/fspeed.txt'
LOCATION_FILE = '/var/www/html/location.php'

class GPS:
    ''' GSP class '''
    def __init__(self, beetle):
        self.beetle = beetle
        self.last_phone_home = 0.0
        gpsd.connect()
        self.beetle.logger.info('GPS poller initialized')

    def poll(self):
        try:
            ''' webui as often as possible '''
            packet = gpsd.get_current()
            position_str = '%.6f,%.9f' % (packet.lat, packet.lon)
            self.beetle.state.set('location', position_str)
            hspeed = packet.hspeed * 2.237
            with open(HSPEED_FILE, 'w+') as fout:
                fout.write('%.0f mph' % hspeed)
                fout.flush()
                os.fsync(fout.fileno())
            fspeed = packet.speed() * 2.237
            with open(FSPEED_FILE, 'w+') as fout:
                fout.write('%.0f mph' % hspeed)
                fout.flush()
                os.fsync(fout.fileno())

            ''' phone home every 5 minutes '''
            now = time.time()
            delta = now - self.last_phone_home
            if delta < 300.0 and delta > 0.0:
                return
            self.last_phone_home = now
            with open(LOCATION_FILE, 'w+') as fout:
                fout.write('<?php header(\'Location: %s\'); ?>' % packet.map_url())
                fout.flush()
                os.fsync(fout.fileno())
            cmd = ('scp -P 2222 %s pi@crystalpalace.ddns.net'
                   ':/var/www/html/beetle/index.php > /dev/null' % LOCATION_FILE)
            subprocess.call(cmd, shell=True)
        except gpsd.NoFixError:
            self.beetle.logger.error('gps signal too low')
