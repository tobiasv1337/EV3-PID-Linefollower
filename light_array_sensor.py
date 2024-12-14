from ev3dev2.sensor import Sensor
from ev3dev2.port import LegoPort
from ev3dev2.sound import Sound
import time
import struct

class LightArraySensor:
    """
    A class to interact with the Mindsensors Light Sensor Array (ms-light-array) on ev3dev.
    """
    def __init__(self, port='in1', flipped=False):
        """
        Initialize the Light Sensor Array.
        :param port: Port where the sensor is connected (e.g., 'in1', 'in2').
        """
        self.sound = Sound()

        self.flipped = flipped
        self.max_value = 100 # Values for CAL are in percentage, RAW seems to be too, but is not documented!

        self.port = LegoPort(address=port)
        self.port.mode = 'nxt-i2c'

        self.sensor = None
        for _ in range(10):
            try:
                self.sensor = Sensor(address=port)
                self.mode = "RAW" # The library is broken, thus we need to initialize with RAW mode
                self.sensor.mode = self.mode
                print("Sensor initialized in RAW mode")
                break
            except PermissionError:
                print("PermissionError during initialization. Retrying...")
                time.sleep(1)

        if self.sensor is None:
            raise RuntimeError("Failed to initialize the sensor after 10 retries")

    def calibrate_white(self):
        self.sensor.command = 'CAL-WHITE'

    def calibrate_black(self):
        self.sensor.command = 'CAL-BLACK'

    def calibrate(self):
        self.sound.speak("Calibrate white")
        input("Place sensor on white and press Enter.")
        self.calibrate_white()

        self.sound.speak("Calibrate black")
        input("Place sensor on black and press Enter.")
        self.calibrate_black()

        self.sound.speak("Calibration complete")

    def set_frequency(self, mode):
        if mode not in ['50HZ', '60HZ', 'UNIVERSAL']:
            raise ValueError("Invalid frequency mode. Use '50HZ', '60HZ', or 'UNIVERSAL'.")
        self.sensor.command = mode

    def sleep(self):
        self.sensor.command = 'SLEEP'

    def wake(self):
        while True:
            try:
                self.sensor.command = 'WAKE'
                break
            except Exception as e:
                time.sleep(0.1)

    def set_mode(self, mode):
        if mode not in ["CAL", "RAW"]:
            raise ValueError("Invalid mode. Use 'CAL' or 'RAW'.")
        self.mode = mode
        self.sensor.mode = mode
        print("Sensor mode set to: {}".format(mode))

    def read_data(self):
        """
        Read the raw data from the sensor based on its current format.
        :return: Null if the data is invalid, otherwise a list of values for each light sensor element.
        """
        # Map bin_data_format to struct format and size
        fmt_map = {
            'u8': ('16B', 16),   # Should be: 8 unsigned 8-bit integers (CAL mode). But the library is broken and thus to support both modes, we init the sensor in RAW mode and when switching to CAL mode, we get 16 bytes instead of 8 and discard the last 8 bytes.
            's16': ('8h', 16),   # 8 signed 16-bit integers (RAW mode)
        }

        fmt = self.sensor.bin_data_format
        if fmt not in fmt_map:
            raise ValueError("Unsupported bin_data_format: {}".format(fmt))

        struct_fmt, expected_length = fmt_map[fmt]
        raw = self.sensor.bin_data()

        if len(raw) != expected_length:
            print("WARNING: Expected {} bytes, but got {} bytes. Discarding invalid data.".format(
                expected_length, len(raw)))
            return None

        raw_data = struct.unpack(struct_fmt, raw)

        raw_data = raw_data[:8]  # Discard the last 8 bytes if in CAL mode

        if self.flipped:
            raw_data = raw_data[::-1]

        print("Unpacked sensor data ({}): {}".format(struct_fmt, raw_data))
        return raw_data

    def get_line_position(self):
        """
        Calculate the position of the line relative to the sensor based on the current mode.
        Low values (black) represent the line.
        :return: A float representing the line position (weighted average) or None if invalid data.
        """
        data = self.read_data()
        if data is None:
            print("Invalid data received. Unable to calculate line position.")
            return None # Propagate the error

        # Calculate the inverted data so that low values (black) are weighted more heavily
        inverted_data = [self.max_value - value for value in data]

        weighted_sum = sum(value * (index + 1) for index, value in enumerate(inverted_data))
        total = sum(inverted_data)

        if total == 0:
            return 0.0  # Avoid division by zero
        return weighted_sum / total


if __name__ == "__main__":
    sensor = LightArraySensor(port='in1')

    # Calibrate the sensor
    print("Calibrating the sensor...")
    sensor.calibrate()
    print("Calibration complete.")

    # Set frequency mode to 'UNIVERSAL'
    sensor.set_frequency('UNIVERSAL')

    # Read line position
    while True:
        position = sensor.get_line_position()
        print("Line position: {}".format(position))
        time.sleep(0.1)