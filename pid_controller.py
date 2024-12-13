class PIDController:
    """
    A simple PID Controller class.
    """

    def __init__(self, kp, ki, kd, setpoint=0, output_limits=(None, None)):
        self.kp = kp
        self.ki = ki
        self.kd = kd
        self.setpoint = setpoint
        self.output_limits = output_limits

        self._integral = 0
        self._previous_error = 0
        self._last_output = 0

    def compute(self, current_value):
        error = self.setpoint - current_value

        proportional = self.kp * error

        self._integral += error
        integral = self.ki * self._integral

        derivative = self.kd * (error - self._previous_error)
        self._previous_error = error

        output = proportional + integral + derivative

        min_output, max_output = self.output_limits
        if min_output is not None:
            output = max(min_output, output)
        if max_output is not None:
            output = min(max_output, output)

        self._last_output = output
        return output

    def reset(self):
        self._integral = 0
        self._previous_error = 0
        self._last_output = 0

    def set_setpoint(self, setpoint):
        self.setpoint = setpoint

    def set_output_limits(self, min_output, max_output):
        self.output_limits = (min_output, max_output)