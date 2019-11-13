#!/usr/bin/env python

import socket

from datetime import datetime

def log_print(str):
    ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print '%s %s' % (ts, str)
    LOG.write('%s %s\n' % (ts, str))

class Beetle:
    ''' Integration class for all the components of the car '''
    def __init__(self, location):
        self.location = location

    def gather():
        ''' Gather information locally and from other pi '''

    def process():
        ''' Process gathered information and take actions '''

    def poll():
        ''' Repeat gather and process forever '''
        while True:
            gather()
            process()

def main():

    # The location of the pi determines what its responsibilities are.
    # The hostname is beetle-location.
    location = socket.gethostname().split('-')[1]

    beetle = Beetle(location)
    beetle.poll()

if __name__== '__main__':
    main()
