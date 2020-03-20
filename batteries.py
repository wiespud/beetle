import time
import tca
import nau

BATTERIES = {
    'front': {
        # TCA I2C address
        0x70: {
            # TCA channel
                # Battery pack number
                   # Battery group number
                      # Voltage offset
            0: (1, 1, -0.062), # 6.59
            1: (1, 2, -0.045), # 6.59
            2: (1, 3, -0.064), # 6.59
            3: (1, 4, -0.067), # 6.59
        },
        0x71: {
            0: (1, 5, -0.071), # 6.58
            1: (1, 6, -0.040), # 6.58
            2: (1, 7, -0.008), # 6.56
            # 3: (1, 8, -0.020),
        },
    },
    'back': {
        0x72: {
            0: (2,  9, -0.017), # 6.59
            1: (2, 10, -0.042), # 6.58
            2: (2, 11, -0.030), # 6.58
            3: (2, 12, -0.023), # 6.57
        },
        0x73: {
            0: (2, 13, -0.060), # 6.57
            1: (2, 14, -0.037), # 6.57
            2: (2, 15, -0.079), # 6.57
            3: (2, 16, -0.022), # 6.55
        },
    },
}

class Battery:
    ''' A single battery group corresponding to one BMS board '''
    def __init__(self, pack, group, bus, address, channel, offset, count, limit=0.5):
        self.pack = pack
        self.group = group
        self.bus = bus
        self.address = address
        self.channel = channel
        self.offset = offset
        self.count = count
        self.limit = limit
        self.error = False
        self.errors = [] # Append True if a measurement had an error
        self.temperatures = []
        self.voltages = { 1: [], 2: [] }
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
        return self.voltages[1][-1] + self.voltages[2][-1] + self.offset

    def get_average_voltage(self):
        average_1 = sum(self.voltages[1]) / float(len(self.voltages[1]))
        average_2 = sum(self.voltages[2]) / float(len(self.voltages[2]))
        return average_1 + average_2 + self.offset

    def update_error_history(self):
        self.errors.append(self.error)
        if len(self.errors) > self.count:
            self.errors.pop(0)
        self.error = False

    def check_error_history(self):
        ''' Return True if the errors exceed the limit '''
        errors = sum(1 for error in self.errors if error)
        return (float(errors) / len(self.errors)) > self.limit

    def start_temperature_measurement(self):
        tca.select(self.bus, self.address, self.channel)
        try:
            nau.temperature_setup(self.bus)
            nau.start_measurement(self.bus)
        except IOError:
            self.error = True
        tca.disable(self.bus, self.address)

    def finish_temperature_measurement(self):
        if not self.error:
            tca.select(self.bus, self.address, self.channel)
            try:
                temp = nau.get_temperature(self.bus)
                self.temperatures.append(temp)
                if len(self.temperatures) > self.count:
                    self.temperatures.pop(0)
            except IOError:
                self.error = True
            tca.disable(self.bus, self.address)
        self.update_error_history()

    def start_voltage_measurement(self, nau_ch):
        tca.select(self.bus, self.address, self.channel)
        try:
            nau.voltage_setup(self.bus, nau_ch)
            nau.start_measurement(self.bus)
        except IOError:
            self.error = True
        tca.disable(self.bus, self.address)

    def finish_voltage_measurement(self, nau_ch):
        if not self.error:
            tca.select(self.bus, self.address, self.channel)
            try:
                volts = nau.get_voltage(self.bus)
                self.voltages[nau_ch].append(volts)
                if len(self.voltages[nau_ch]) > self.count:
                    self.voltages[nau_ch].pop(0)
            except IOError:
                self.error = True
            tca.disable(self.bus, self.address)
        self.update_error_history()

class Batteries:
    ''' All batteries being monitored by the BMS '''
    def __init__( self,
                  bus,
                  location,
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
        for address in BATTERIES[location]:
            for channel in BATTERIES[location][address]:
                pack, group, offset = BATTERIES[location][address][channel]
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
        for battery in self.batteries:
            battery.start_temperature_measurement()
        time.sleep(0.5)
        for battery in self.batteries:
            battery.finish_temperature_measurement()
            battery.start_voltage_measurement(1)
        time.sleep(0.5)
        for battery in self.batteries:
            battery.finish_voltage_measurement(1)
            battery.start_voltage_measurement(2)
        time.sleep(0.5)
        for battery in self.batteries:
            battery.finish_voltage_measurement(2)
            if battery.check_error_history():
                print 'ERROR: Exceeded error limit: %s' % battery
                raise OSError
