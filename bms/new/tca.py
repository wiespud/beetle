
def unicast(bus, address, channel):
    bus.write_byte(address, 1 << channel)

def broadcast(bus, address):
    bus.write_byte(address, 0xf)

def disable(bus, address):
    bus.write_byte(address, 0)

def reset(address):
    ''' toggle gpio reset line '''
    return
