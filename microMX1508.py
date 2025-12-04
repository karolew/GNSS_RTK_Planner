import time

from machine import PWM, Pin


class microMX1508:
    """
    A non-blocking motor controller for MX1508 motor driver.
    Features smooth acceleration and minimal resource usage.
    """

    def __init__(self, motor1_pins: tuple, motor2_pins: tuple, freq: int = 1000, accel_rate: int = 10) -> None:
        """Initialize the motors with their control pins.

        Args:
            motor1_pins: Tuple of (in1, in2) pins for motor 1.
            motor2_pins: Tuple of (in1, in2) pins for motor 2.
            freq: PWM frequency in Hz (default 1000).
            accel_rate: Acceleration rate in steps per update (1-100).
        """
        # Motor 1 setup
        self.m1_pwm1 = PWM(Pin(motor1_pins[0]), freq=freq)
        self.m1_pwm2 = PWM(Pin(motor1_pins[1]), freq=freq)

        # Motor 2 setup
        self.m2_pwm1 = PWM(Pin(motor2_pins[0]), freq=freq)
        self.m2_pwm2 = PWM(Pin(motor2_pins[1]), freq=freq)

        # Set PWM duty cycle range.
        self.max_duty = 1023

        # Motor speeds and targets (0 to 100 percent)
        self.m1_current_speed = 0
        self.m1_target_speed = 0
        self.m1_direction = 1  # 1 forward, -1 reverse

        self.m2_current_speed = 0
        self.m2_target_speed = 0
        self.m2_direction = 1

        # Acceleration parameters
        self.accel_rate = max(1, min(100, accel_rate))  # Constrain between 1-100

        # Timing for non-blocking operation
        self.last_update = time.ticks_ms()
        self.update_interval = 20  # milliseconds between updates

        # Initialize motors to stopped state
        self._apply_motor1_speed(0)
        self._apply_motor2_speed(0)

    def _apply_motor1_speed(self, speed_percent):
        duty = int(speed_percent * self.max_duty / 100)

        if self.m1_direction == 1:  # Forward
            self.m1_pwm1.duty(duty)
            self.m1_pwm2.duty(0)
        else:  # Reverse
            self.m1_pwm1.duty(0)
            self.m1_pwm2.duty(duty)

    def _apply_motor2_speed(self, speed_percent):
        duty = int(speed_percent * self.max_duty / 100)

        if self.m2_direction == 1:  # Forward
            self.m2_pwm1.duty(duty)
            self.m2_pwm2.duty(0)
        else:  # Reverse
            self.m2_pwm1.duty(0)
            self.m2_pwm2.duty(duty)

    def set_motor1(self, speed):
        """Set target speed for motor 1.
        """
        if speed < 0:
            self.m1_direction = -1
            self.m1_target_speed = min(100, abs(speed))
        else:
            self.m1_direction = 1
            self.m1_target_speed = min(100, speed)

    def set_motor2(self, speed):
        """Set target speed for motor 2.
        """
        if speed < 0:
            self.m2_direction = -1
            self.m2_target_speed = min(100, abs(speed))
        else:
            self.m2_direction = 1
            self.m2_target_speed = min(100, speed)

    def stop(self):
        """Stop both motors (set target speed to 0)
        """
        self.m1_target_speed = 0
        self.m2_target_speed = 0

    def stop_immediate(self):
        """Immediately stop both motors (no smooth deceleration)
        """
        self.m1_current_speed = 0
        self.m2_current_speed = 0
        self.m1_target_speed = 0
        self.m2_target_speed = 0
        self._apply_motor1_speed(0)
        self._apply_motor2_speed(0)

    def update(self):
        """Update motor speeds according to targets (non-blocking).
        Call this method frequently in your main loop.
        """
        current_time = time.ticks_ms()

        # Only update at specified intervals to reduce CPU usage
        if time.ticks_diff(current_time, self.last_update) < self.update_interval:
            return False

        self.last_update = current_time
        motors_changed = False

        # Update motor 1 speed
        if self.m1_current_speed < self.m1_target_speed:
            self.m1_current_speed = min(self.m1_target_speed,
                                        self.m1_current_speed + self.accel_rate)
            self._apply_motor1_speed(self.m1_current_speed)
            motors_changed = True
        elif self.m1_current_speed > self.m1_target_speed:
            self.m1_current_speed = max(self.m1_target_speed,
                                        self.m1_current_speed - self.accel_rate)
            self._apply_motor1_speed(self.m1_current_speed)
            motors_changed = True

        # Update motor 2 speed
        if self.m2_current_speed < self.m2_target_speed:
            self.m2_current_speed = min(self.m2_target_speed,
                                        self.m2_current_speed + self.accel_rate)
            self._apply_motor2_speed(self.m2_current_speed)
            motors_changed = True
        elif self.m2_current_speed > self.m2_target_speed:
            self.m2_current_speed = max(self.m2_target_speed,
                                        self.m2_current_speed - self.accel_rate)
            self._apply_motor2_speed(self.m2_current_speed)
            motors_changed = True

        return motors_changed

    def set_acceleration_rate(self, rate):
        self.accel_rate = max(1, min(100, rate))

    def set_update_interval(self, interval_ms):
        self.update_interval = max(5, interval_ms)  # Minimum 5ms
