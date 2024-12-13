from ev3dev2.button import Button
from ev3dev2.display import Display
from ev3dev2.sound import Sound
from light_array_sensor import LightArraySensor
from ev3_motor import EV3Motor
from pid_controller import PIDController
from ev3dev2.motor import OUTPUT_A, OUTPUT_B
import time

class LineFollower:
    def __init__(self):
        # Initialize components
        self.sensor = LightArraySensor(port='in1')
        self.left_motor = EV3Motor(port=OUTPUT_A, motor_type='large')
        self.right_motor = EV3Motor(port=OUTPUT_B, motor_type='large')
        self.pid = PIDController(kp=1.2, ki=0.01, kd=0.2, setpoint=4.5, output_limits=(-50, 50))

        self.btn = Button()
        self.display = Display()
        self.sound = Sound()

        # State variables
        self.running = False
        self.debug_mode = True

        self.base_speed = 30  # Base speed for both motors
        self.max_speed = 100  # Maximum allowed motor speed

    def scale_motor_speeds(self, left_speed, right_speed):
        max_current_speed = max(abs(left_speed), abs(right_speed))

        # If the maximum exceeds the allowable speed, scale both speeds proportionally
        if max_current_speed > self.max_speed:
            scaling_factor = self.max_speed / max_current_speed
            left_speed *= scaling_factor
            right_speed *= scaling_factor

        # Prevent issues due to rounding errors
        left_speed = max(-self.max_speed, min(self.max_speed, left_speed))
        right_speed = max(-self.max_speed, min(self.max_speed, right_speed))

        return left_speed, right_speed

    def calibrate_sensor(self):
        self.sound.speak("Calibrate white")
        input("Place sensor on white and press Enter.")
        self.sensor.calibrate_white()

        self.sound.speak("Calibrate black")
        input("Place sensor on black and press Enter.")
        self.sensor.calibrate_black()

        self.sound.speak("Calibration complete")

    def debug_visualization(self, sensor_data):
        self.display.clear()

        # Draw sensor output as bars
        for i, value in enumerate(sensor_data):
            bar_height = int((value / 255) * 64)
            self.display.rectangle(
            x=i * 20,
            y=64 - bar_height,
            width=18,
            height=bar_height,
            fill=True
        )

        # Show calculated line position
        line_position = self.sensor.get_line_position()
        self.display.text_pixels("Line Pos: {:.2f}.format(line_position)", x=0, y=70, text_color='white')
        self.display.update()

    def toggle_running_state(self):
        if self.btn.enter:
            self.running = not self.running
            if self.running:
                self.sound.speak("Line following enabled")
            else:
                self.sound.speak("Line following disabled")
            time.sleep(0.5)  # Debounce

    def follow_line(self):
        try:
            while True:
                self.toggle_running_state()

                sensor_data = self.sensor.read_raw()

                if self.debug_mode:
                    self.debug_visualization(sensor_data)

                if self.running:
                    line_position = self.sensor.get_line_position()
                    correction = self.pid.compute(line_position)

                    base_speed = 30
                    left_speed = base_speed - correction
                    right_speed = base_speed + correction

                    left_speed, right_speed = self.scale_motor_speeds(left_speed, right_speed)

                    self.left_motor.set_speed(left_speed)
                    self.right_motor.set_speed(right_speed)
                else:
                    self.left_motor.stop()
                    self.right_motor.stop()

                time.sleep(0.01)
        except KeyboardInterrupt:
            self.left_motor.stop()
            self.right_motor.stop()
            self.display.clear()
            self.display.text_pixels("Exiting...", x=0, y=0, text_color='white')
            self.display.update()
            self.sound.speak("Goodbye")


if __name__ == "__main__":
    follower = LineFollower()

    follower.calibrate_sensor()

    follower.follow_line()