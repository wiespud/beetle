import tca
import nau

BATTERIES = {
    # TCA I2C address
    0x70: {
        # TCA channel
            # Battery pack number
               # Battery group number
                  # Voltage offset
        0: (1, 1, -0.064),
        1: (1, 2, -0.049),
        2: (1, 3, -0.071),
        3: (1, 4, -0.070),
    },
    0x71: {
        0: (1, 5, -0.074),
        1: (1, 6, -0.050),
        2: (1, 7, -0.023),
        3: (1, 8, -0.012),
    },
    0x72: {
        0: (2, 9, -0.027),
        1: (2, 10, -0.038),
        2: (2, 11, -0.024),
        3: (2, 12, -0.012),
    },
    0x73: {
        0: (2, 13, -0.038),
        1: (2, 14, -0.016),
        2: (2, 15, -0.087),
        3: (2, 16, -0.001),
    },
}

class Battery:
    ''' A single battery group corresponding to one BMS board '''
    def __init__(self, pack, group, address, channel, offset, count):
        self.pack = pack
        self.group = group
        self.address = address
        self.channel = channel
        self.offset = offset
        self.count = count
        self.temperatures = []
        self.temperature_sum = 0.0
        self.voltages = []
        self.voltage_sum = 0.0

    def __str__(self):
        return 'group %d, address 0x%02X, channel %d, offset %.03f' % (self.group, self.address, self.channel, self.offset)

    def get_temperature(self):
        return 0.0

    def get_voltage(self):
        return 0.0

class Batteries:
    ''' All batteries being monitored by the BMS '''
    def __init__(self, count, under_error, under_warning, over_warning, over_error, temp_warning, temp_error):
        self.under_error = under_error
        self.under_warning = under_warning
        self.over_warning = over_warning
        self.over_error = over_error
        self.temp_warning = temp_warning
        self.temp_error = temp_error
        self.batteries = []
        for address in BATTERIES:
            for channel in BATTERIES[address]:
                pack, group, offset = BATTERIES[address][channel]
                battery = Battery(pack, group, address, channel, offset, count)
                self.batteries.append(battery)

    def battery_iter(self):
        for battery in self.batteries:
            yield battery

    def do_measurements(self):
        