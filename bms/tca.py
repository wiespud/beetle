'''
Interface to TCA9546ADR I2C switch
http://www.ti.com/lit/ds/symlink/tca9546a.pdf
'''

def select(bus, address, channel):
    bus.write_byte(address, 1 << channel)

def disable(bus, address):
    bus.write_byte(address, 0)

def reset(address):
    ''' toggle gpio reset line '''
    return
