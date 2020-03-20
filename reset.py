#!/usr/bin/env python

import smbus

import batteries

def main():
    bus = smbus.SMBus(1)
    batts = batteries.Batteries(bus)

if __name__== '__main__':
    main()
