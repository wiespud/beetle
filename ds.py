'''
Interface to DS18B20 digital temperature sensor
https://datasheets.maximintegrated.com/en/ds/DS18B20.pdf
https://pinout.xyz/pinout/1_wire
'''

def get_temp(address):
    reading_valid = False
    temperature = 0.0
    with open('/sys/bus/w1/devices/%s/w1_slave' % address) as fin:
        for line in fin:
            if 'YES' in line:
                reading_valid = True
            if 't=' in line:
                t = line.split('t=')[1].strip()
                temperature = float(t) / 1000
    if reading_valid and temperature > 0.0:
        return temperature
    raise IOError # failed open for no such file also raises IOError
