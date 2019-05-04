#!/usr/bin/env python

import batteries
# import drok
# import ds

def main():
    batts = batteries.Batteries(10, 5.8, 6.0, 8.0, 8.2, 50.0, 60.0)
    for batt in batts.battery_iter():
        print batt

if __name__== '__main__':
    main()
