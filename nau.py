'''
Interface to NAU7802SGI ADC
http://www.nuvoton.com/resource-files/NAU7802%20Data%20Sheet%20V1.7.pdf
'''

import time

ADDR_NAU = 0x2a

def reset(bus):
    bus.write_byte_data(ADDR_NAU, 0x00, 0x01) # hold in reset
    time.sleep(0.1)
    bus.write_byte_data(ADDR_NAU, 0x00, 0x00) # release reset

def chip_setup(bus):
    reset(bus)
    bus.write_byte_data(ADDR_NAU, 0x00, 0x02) # power up digital
    count = 10
    while True:
        if count == 0:
            return False
        count -= 1
        time.sleep(0.1)
        bus.write_byte(ADDR_NAU, 0x00) # read register 0
        data = bus.read_byte(ADDR_NAU)
        if data & 0x08:
            break
    bus.write_byte_data(ADDR_NAU, 0x00, 0x82) # internal LDO, power up digital
    bus.write_byte_data(ADDR_NAU, 0x01, 0x01) # PGA gain 2x for temperature sensor
    bus.write_byte_data(ADDR_NAU, 0x15, 0x30) # CLK_CHP off
    bus.write_byte_data(ADDR_NAU, 0x00, 0x86) # internal LDO, power up analog, power up digital
    return True

def temperature_setup(bus):
    bus.write_byte_data(ADDR_NAU, 0x1B, 0x00) # PGA bypass disable
    bus.write_byte_data(ADDR_NAU, 0x11, 0x02) # Switch to temperature sensor

def voltage_setup(bus, ch):
    bus.write_byte_data(ADDR_NAU, 0x1B, 0x10) # PGA bypass enable
    bus.write_byte_data(ADDR_NAU, 0x11, 0x00) # Switch to inputs
    if ch == 1:
        bus.write_byte_data(ADDR_NAU, 0x02, 0x00) # Ch1
    elif ch == 2:
        bus.write_byte_data(ADDR_NAU, 0x02, 0x80) # Ch2
    else:
        print 'ERROR: Invalid channel %s for NAU7802SGI' % ch
        raise OSError

def voltage_setup_1(bus):
    bus.write_byte_data(ADDR_NAU, 0x1B, 0x10) # PGA bypass enable
    bus.write_byte_data(ADDR_NAU, 0x11, 0x00) # Switch to inputs
    bus.write_byte_data(ADDR_NAU, 0x02, 0x00) # Ch1

def voltage_setup_2(bus):
    bus.write_byte_data(ADDR_NAU, 0x1B, 0x10) # PGA bypass enable
    bus.write_byte_data(ADDR_NAU, 0x11, 0x00) # Switch to inputs
    bus.write_byte_data(ADDR_NAU, 0x02, 0x80) # Ch2

def start_measurement(bus):
    bus.write_byte_data(ADDR_NAU, 0x00, 0x96) # Start cycle

def get_measurement(bus):
    count = 10
    while True:
        if count == 0:
            return False
        count -= 1
        data = bus.read_byte(ADDR_NAU)
        if data & 0x20:
            break
    bus.write_byte(ADDR_NAU, 0x12)
    b2 = bus.read_byte(ADDR_NAU)
    bus.write_byte(ADDR_NAU, 0x13)
    b1 = bus.read_byte(ADDR_NAU)
    bus.write_byte(ADDR_NAU, 0x14)
    b0 = bus.read_byte(ADDR_NAU)
    return ((b2 << 16) + (b1 << 8) + b0)

def get_voltage(bus):
    measurement = get_measurement(bus)
    voltage = 9.0 * float(measurement) / float(2**24)
    return voltage

def get_temperature(bus):
    measurement = get_measurement(bus)
    temperature =  (4.5 * float(measurement) / float(2**24)) / float(0.00036) - 277.78
    return temperature
