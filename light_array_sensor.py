from ev3dev2.sensor import Sensor
from ev3dev2.port import LegoPort
from ev3dev2.sound import Sound
import time

class LightArraySensor:
    """
    A class to interact with the Mindsensors Light Sensor Array (ms-light-array) on ev3dev.
    """
    def __init__(self, port='in1'):
        """
        Initialize the Light Sensor Array.
        :param port: Port where the sensor is connected (e.g., 'in1', 'in2').
        """
        self.port = LegoPort(address=port)
        self.port.mode = 'nxt-i2c'

        self.sensor = Sensor(address=port)
        self.mode = "CAL"

        self.sound = Sound()

    def calibrate_white(self):
        self.sensor.command = 'CAL-WHITE'

    def calibrate_black(self):
        self.sensor.command = 'CAL-BLACK'

    def calibrate_sensor(self):
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
        self.sensor.poll_ms = 0  # Required before putting the sensor to sleep
        self.sensor.command = 'SLEEP'

    def wake(self):
        self.sensor.command = 'WAKE'

    def set_mode(self, mode):
        if mode not in ["CAL", "RAW"]:
            raise ValueError("Invalid mode. Use 'CAL' or 'RAW'.")
        self.mode = mode

    def read_data(self):
        """
        Read the data from the sensor based on the current mode.
        :return: A list of 8 values representing the light intensity from each sensor element.
        """
        return self.sensor.bin_data('B' * 8)

    def get_line_position(self):
        """
        Calculate the position of the line relative to the sensor based on the current mode.
        :return: A float representing the line position (weighted average).
        """
        data = self.read_data()
        weighted_sum = sum(value * (index + 1) for index, value in enumerate(data))
        total = sum(data)
        if total == 0:
            return 0  # Avoid division by zero
        return weighted_sum / total


if __name__ == "__main__":
    sensor = LightArraySensor(port='in1')

    # Calibrate the sensor
    print("Calibrating the sensor...")
    print("Place the sensor over a white surface within 5 seconds.")
    time.sleep(5)
    sensor.calibrate_white()
    print("Sucessfully calibrated white.")
    print("Place the sensor over a black surface within 5 seconds.")
    time.sleep(5)
    sensor.calibrate_black()
    time.sleep(1)
    print("Sucessfully calibrated black.")
    print("Calibration complete.")

    # Set frequency mode to 'UNIVERSAL'
    sensor.set_frequency('UNIVERSAL')

    # Read line position
    while True:
        position = sensor.get_line_position()
        print("Line position: {}".format(position))
        time.sleep(0.1)