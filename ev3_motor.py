from ev3dev2.motor import LargeMotor, MediumMotor, OUTPUT_A, OUTPUT_B, OUTPUT_C, OUTPUT_D
from ev3dev2.motor import SpeedPercent, SpeedDPS, SpeedRPM
import time

class EV3Motor:
    """
    A simple library for controlling LEGO EV3 motors.
    """

    def __init__(self, port, motor_type='large'):
        """
        Initialize the motor.

        :param port: The motor port (e.g., OUTPUT_A, OUTPUT_B, OUTPUT_C, OUTPUT_D).
        :param motor_type: The type of motor ('large' or 'medium').
        """
        if motor_type == 'large':
            self.motor = LargeMotor(port)
        elif motor_type == 'medium':
            self.motor = MediumMotor(port)
        else:
            raise ValueError("Invalid motor type. Use 'large' or 'medium'.")


    def stop(self, brake=True):
        self.motor.off(brake=brake)

    def run_to_position(self, position, speed=50, brake=True):
        """
        :param position: Target position in degrees.
        :param speed: Speed percentage (-100 to 100).
        :param brake: Whether to brake when the position is reached.
        """
        self.motor.on_to_position(SpeedPercent(speed), position, brake=brake)

    def run_timed(self, time_ms, speed=50):
        """
        :param time_ms: Time in milliseconds.
        :param speed: Speed percentage (-100 to 100).
        """
        self.motor.on_for_seconds(SpeedPercent(speed), time_ms / 1000)

    def run_to_rel_position(self, rel_position, speed=50, brake=True):
        """
        :param rel_position: Target relative position in degrees.
        :param speed: Speed percentage (-100 to 100).
        :param brake: Whether to brake when the position is reached.
        """
        self.motor.on_for_degrees(SpeedPercent(speed), rel_position, brake=brake)

    def set_speed(self, speed):
        """
        :param speed: Speed percentage (-100 to 100).
        """
        self.motor.on(SpeedPercent(speed))

    def get_position(self):
        """
        :return: Current position in degrees.
        """
        return self.motor.position

    def reset_position(self):
        """
        Reset the motor's position to 0 degrees.
        """
        self.motor.reset()



if __name__ == "__main__":
    motor = EV3Motor(port=OUTPUT_A, motor_type='large')

    print("Running motor at 50% speed for 2 seconds...")
    motor.set_speed(50)
    time.sleep(2)

    print("Stopping motor with brake...")
    motor.stop(brake=True)
    time.sleep(2)

    print("Running to position 360 degrees...")
    motor.run_to_position(position=360, speed=75)

    print("Resetting position...")
    motor.reset_position()

    print("Running for 2 seconds at 60% speed with timed mode...")
    motor.run_timed(time_ms=2000, speed=60)

    position = motor.get_position()
    print("Current position: {} degrees".format(position))