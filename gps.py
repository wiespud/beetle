'''
Interface to GPS receiver

https://github.com/MartijnBraam/gpsd-py3/blob/master/DOCS.md
'''

import gpsd
import os

HSPEED_FILE = '/var/www/html/hspeed.txt'
FSPEED_FILE = '/var/www/html/fspeed.txt'

class GPS:
    ''' GSP class '''
    def __init__(self, logger):
        self.logger = logger
        gpsd.connect()

    def as_often_as_possible(self):
        try:
            packet = gpsd.get_current()
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
        except gpsd.NoFixError:
            self.logger.error('gps could not connect to enough satellites')
