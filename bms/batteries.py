import time
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
        1: (1, 6, -0.048),
        2: (1, 7, -0.022),
        3: (1, 8, -0.012),
    },
    0x72: {
        # 0: (2,  9, -0.017),
        # 1: (2, 10, -0.029),
        2: (2, 11, -0.021),
        3: (2, 12, -0.013),
    },
    0x73: {
        0: (2, 13, -0.060),
        1: (2, 14, -0.024),
        2: (2, 15, -0.109),
        3: (2, 16, -0.016),
    },
}

class Battery:
    ''' A single battery group corresponding to one BMS board '''
    def __init__(self, pack, group, bus, address, channel, offset, count):
        self.pack = pack
        self.group = group
        self.bus = bus
        self.address = address
        self.channel = channel
        self.offset = offset
        self.count = count
        self.temperatures = []
        self.voltages_1 = []
        self.voltages_2 = []
        tca.select(bus, address, channel)
        if not nau.chip_setup(bus):
            print 'ERROR: Chip setup failed on %s' % self
            tca.disable(bus, address)
            raise OSError
        tca.disable(bus, address)

    def __str__(self):
        return 'group %d, address 0x%02X, channel %d, offset %.03f' % (self.group, self.address, self.channel, self.offset)

    def get_group(self):
        return self.group

    def get_last_temperature(self):
        return self.temperatures[-1]

    def get_average_temperature(self):
        return sum(self.temperatures) / float(len(self.temperatures))

    def get_last_voltage(self):
        return self.voltages_1[-1] + self.voltages_2[-1] + self.offset

    def get_average_voltage(self):
        average_1 = sum(self.voltages_1) / float(len(self.voltages_1))
        average_2 = sum(self.voltages_2) / float(len(self.voltages_2))
        return average_1 + average_2 + self.offset

    def check_for_faults(self):
        return False

    def start_temperature_measurement(self):
        tca.select(self.bus, self.address, self.channel)
        nau.temperature_setup(self.bus)
        nau.start_measurement(self.bus)
        tca.disable(self.bus, self.address)

    def finish_temperature_measurement(self):
        tca.select(self.bus, self.address, self.channel)
        temp = nau.get_temperature(self.bus)
        self.temperatures.append(temp)
        if len(self.temperatures) > self.count:
            self.temperatures.pop(0)
        tca.disable(self.bus, self.address)

    def start_voltage_1_measurement(self):
        tca.select(self.bus, self.address, self.channel)
        nau.voltage_setup_1(self.bus)
        nau.start_measurement(self.bus)
        tca.disable(self.bus, self.address)

    def finish_voltage_1_measurement(self):
        tca.select(self.bus, self.address, self.channel)
        volts = nau.get_voltage(self.bus)
        self.voltages_1.append(volts)
        if len(self.voltages_1) > self.count:
            self.voltages_1.pop(0)
        tca.disable(self.bus, self.address)

    def start_voltage_2_measurement(self):
        tca.select(self.bus, self.address, self.channel)
        nau.voltage_setup_2(self.bus)
        nau.start_measurement(self.bus)
        tca.disable(self.bus, self.address)

    def finish_voltage_2_measurement(self):
        tca.select(self.bus, self.address, self.channel)
        volts = nau.get_voltage(self.bus)
        self.voltages_2.append(volts)
        if len(self.voltages_2) > self.count:
            self.voltages_2.pop(0)
        tca.disable(self.bus, self.address)

class Batteries:
    ''' All batteries being monitored by the BMS '''
    def __init__( self,
                  bus,
                  count=10,
                  under_emergency=0.0,
                  under_error=0.0,
                  under_warning=0.0,
                  over_warning=0.0,
                  over_error=0.0,
                  over_emergency=0.0,
                  temp_warning=0.0,
                  temp_error=0.0,
                  temp_emergency=0.0,
                  init_group=0 ):
        self.bus = bus
        self.under_emergency = under_emergency
        self.under_error = under_error
        self.under_warning = under_warning
        self.over_warning = over_warning
        self.over_error = over_error
        self.over_emergency = over_emergency
        self.temp_warning = temp_warning
        self.temp_error = temp_error
        self.temp_emergency = temp_emergency
        self.batteries = []
        for address in BATTERIES:
            for channel in BATTERIES[address]:
                pack, group, offset = BATTERIES[address][channel]
                if init_group == 0 or group == init_group:
                    battery = Battery(pack, group, bus, address, channel, offset, count)
                    self.batteries.append(battery)

    def battery_iter(self):
        for battery in self.batteries:
            yield battery

    def get_battery(self, group):
        for battery in self.batteries:
            if battery.get_group() == group:
                return battery

    def do_measurements(self):
        try:
            for battery in self.batteries:
                battery.start_temperature_measurement()
            time.sleep(0.5)
            for battery in self.batteries:
                battery.finish_temperature_measurement()
                battery.start_voltage_1_measurement()
            time.sleep(0.5)
            for battery in self.batteries:
                battery.finish_voltage_1_measurement()
                battery.start_voltage_2_measurement()
            time.sleep(0.5)
            for battery in self.batteries:
                battery.finish_voltage_2_measurement()
        except IOError:
            print 'ERROR: %s' % battery
            raise
