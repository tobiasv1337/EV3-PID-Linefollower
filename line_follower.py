try:
    from ev3dev2.display import Display
    DISPLAY_AVAILABLE = True
except ImportError:
    DISPLAY_AVAILABLE = False

from ev3dev2.button import Button
from ev3dev2.sound import Sound
from light_array_sensor import LightArraySensor
from ev3_motor import EV3Motor
from pid_controller import PIDController
from ev3dev2.motor import OUTPUT_A, OUTPUT_B
import time
import sys
import select

class LineFollower:
    def __init__(self):
        # Constants
        self.base_speed = 10  # Base speed for both motors
        self.max_speed = 100  # Maximum allowed motor speed
        self.scaling_factor = 1.0  # Internal variable for scaling motor speeds

        # Initialize components
        self.sensor = LightArraySensor(port='in1', flipped=True)
        self.left_motor = EV3Motor(port=OUTPUT_A, motor_type='large')
        self.right_motor = EV3Motor(port=OUTPUT_B, motor_type='large')
        self.pid = PIDController(kp=6.5, ki=0.0, kd=6.5, setpoint=4.5, output_limits=(-self.max_speed, self.max_speed))

        self.btn = Button()
        self.sound = Sound()

        if DISPLAY_AVAILABLE:
            self.display = Display()

        # State variables
        self.running = False
        self.debug_mode = True

        self.loop_frequency = 0.0
        self.inverted_display = True

    def scale_motor_speeds(self, left_speed, right_speed):
        max_current_speed = max(abs(left_speed), abs(right_speed))

        # If the maximum exceeds the allowable speed, scale both speeds proportionally
        if max_current_speed > self.max_speed:
            self.scaling_factor = self.max_speed / max_current_speed
            left_speed *= self.scaling_factor
            right_speed *= self.scaling_factor
        else:
            self.scaling_factor = 1.0

        # Prevent issues due to rounding errors
        left_speed = max(-self.max_speed, min(self.max_speed, left_speed))
        right_speed = max(-self.max_speed, min(self.max_speed, right_speed))

        return left_speed, right_speed

    def debug_visualization(self, sensor_data):
        """
        Visualize sensor data and relevant system information on the EV3 display.
        Handles None values and adjusts for RAW/CAL scaling differences.
        """
        if not DISPLAY_AVAILABLE:
            return

        self.display.clear()

        screen_width = 178
        screen_height = 128

        if sensor_data is None:
            self.display.draw.text((5, 10), "Invalid sensor data", fill='black')
            self.display.update()
            return

        num_sensors = len(sensor_data)
        bar_width = screen_width // num_sensors
        max_bar_height = 64  # Half of the screen height reserved for sensor bars

        for i, value in enumerate(sensor_data):
            normalized_value = max(0, min(value, self.sensor.max_value))  # Clamp to [0, max_value]
            bar_height = int(((self.sensor.max_value - normalized_value) / self.sensor.max_value) * max_bar_height)

            if self.inverted_display:
                x1 = screen_width - ((i + 1) * bar_width)
                x2 = x1 + bar_width - 2
            else:
                x1 = i * bar_width
                x2 = x1 + bar_width - 2

            y1 = screen_height // 2 - bar_height
            y2 = screen_height // 2

            self.display.draw.rectangle((x1, screen_height // 2 - max_bar_height, x2, y2), outline='black')
            self.display.draw.rectangle((x1, y1, x2, y2), fill='black')

        line_position = self.sensor.get_line_position()

        if line_position is not None:
            if self.inverted_display:
                line_x = screen_width - int((line_position / num_sensors) * screen_width)
            else:
                line_x = int((line_position / num_sensors) * screen_width)

            self.display.draw.line((line_x, 0, line_x, max_bar_height), fill='black', width=2)
            self.display.draw.text((5, 94), "Line Pos: {:.2f} | Freq: {:.1f} Hz".format(line_position, self.loop_frequency), fill='black')
        else:
            self.display.draw.text((5, 94), "Line Pos: N/A | Freq: {:.1f} Hz".format(self.loop_frequency), fill='black')

        self.display.draw.text((5, 66), "Mode: {} | State: {}".format(
            self.sensor.mode,
            "Run" if self.running else "Stop"), fill='black')

        self.display.draw.text((5, 80), "Kp: {:.2f} Ki: {:.2f} Kd: {:.2f}".format(self.pid.kp, self.pid.ki, self.pid.kd), fill='black')

        left_motor_speed = self.left_motor.motor.speed
        right_motor_speed = self.right_motor.motor.speed
        self.display.draw.text((5, 108), "L: {} R: {} | Scale: {:.2f}".format(
            left_motor_speed,
            right_motor_speed,
            self.scaling_factor), fill='black')

        self.display.update()

    def toggle_running_state(self):
        if self.btn.enter:
            self.running = not self.running
            if self.running:
                self.sound.speak("Line following enabled")
            else:
                self.sound.speak("Line following disabled")
            time.sleep(0.5)  # Debounce
    
    def toggle_sensor_mode(self):
        if self.btn.up:
            new_mode = "RAW" if self.sensor.mode == "CAL" else "CAL"
            self.sensor.set_mode(new_mode)
            if new_mode == "CAL":
                self.sound.speak("Calibration mode enabled")
            else:
                self.sound.speak("Raw sensor data mode enabled")
            time.sleep(0.5)  # Debounce

    def manual_calibration(self):
        if self.btn.down:
            self.sound.speak("Entering manual calibration mode.")
            self.sensor.calibrate()
            self.sound.speak("Manual calibration complete.")
            time.sleep(0.5)  # Debounce

    def toggle_debug_mode(self):
        if self.btn.left:
            self.debug_mode = not self.debug_mode
            if self.debug_mode:
                self.sound.speak("Debug mode enabled")
            else:
                self.sound.speak("Debug mode disabled")
            time.sleep(0.5)  # Debounce

    def handle_button_presses(self):
        self.toggle_running_state()
        self.toggle_sensor_mode()
        self.manual_calibration()
        self.toggle_debug_mode()


    def check_for_command(self):
        """
        Check for a command from the SSH terminal to update PID gains or robot speed.
        """
        if select.select([sys.stdin], [], [], 0)[0]:
            user_input = sys.stdin.readline().strip()
            try:
                if user_input.startswith("p"):
                    self.pid.kp = float(user_input[1:])
                    print("Updated Kp to {}".format(self.pid.kp))
                elif user_input.startswith("i"):
                    self.pid.ki = float(user_input[1:])
                    print("Updated Ki to {}".format(self.pid.ki))
                elif user_input.startswith("d"):
                    self.pid.kd = float(user_input[1:])
                    print("Updated Kd to {}".format(self.pid.kd))
                elif user_input.startswith("s"):
                    self.base_speed = float(user_input[1:])
                    print("Updated base speed to {}".format(self.base_speed))
                else:
                    print("Invalid command. Use p, i, d, or s followed by a value.")
            except ValueError:
                print("Invalid value. Please enter a numeric value after p, i, d, or s.")


    def follow_line(self):
        """
        Core function for line following.
        Visualization will only be used if display is available.
        """
        try:
            last_line_position = None
            loop_start_time = time.time()
            loop_counter = 0

            while True:
                self.handle_button_presses()
                self.check_for_command()

                sensor_data = self.sensor.read_data()
                line_position = self.sensor.get_line_position()

                if self.debug_mode and DISPLAY_AVAILABLE:
                    loop_counter += 1
                    elapsed_time = time.time() - loop_start_time
                    if elapsed_time >= 1.0:  # Update frequency every second
                        self.loop_frequency = loop_counter / elapsed_time
                        loop_start_time = time.time()
                        loop_counter = 0

                    self.debug_visualization(sensor_data)

                if self.running:
                    if sensor_data is None:
                        print("Skipping control update due to invalid sensor data.")
                        continue

                    if line_position is None:
                        if last_line_position is not None:
                            if last_line_position < 4.5:
                                print("Tracking lost. Trying to recover to the left.")
                                self.left_motor.set_speed(self.base_speed)
                                self.right_motor.set_speed(-self.base_speed)
                            else:
                                print("Tracking lost. Trying to recover to the right.")
                                self.left_motor.set_speed(-self.base_speed)
                                self.right_motor.set_speed(self.base_speed)
                        continue

                    correction = self.pid.compute(line_position)

                    left_speed = self.base_speed + correction
                    right_speed = self.base_speed - correction

                    left_speed, right_speed = self.scale_motor_speeds(left_speed, right_speed)

                    self.left_motor.set_speed(left_speed)
                    self.right_motor.set_speed(right_speed)
                else:
                    self.left_motor.stop()
                    self.right_motor.stop()

                last_line_position = line_position
                #time.sleep(0.01)
        except KeyboardInterrupt:
            self.left_motor.stop()
            self.right_motor.stop()
            if DISPLAY_AVAILABLE:
                self.display.clear()
                self.display.text_pixels("Exiting...", x=0, y=0, text_color='white')
                self.display.update()
            self.sound.speak("Goodbye")


def main():
    follower = LineFollower()
    follower.follow_line()


if __name__ == "__main__":
    main()
