import sys

from machine import I2C

from logger import get_logger
from microIMU9v6.imu9v6 import MinIMU9v6
from microMX1508.microMX1508 import microMX1508
from microNMEA.microNMEA import Precise


class Movement:
    def __init__(self, motor_a = (27, 14), motor_b = (12, 13),
                 tolerance_heading = 5, debug_print: bool = True) -> None:
        self.tolerance_heading = tolerance_heading
        self.motors = None
        self.status = "S"   # S - Stop, L = Left, R - Right,F - Forward
        self.debug_print = debug_print
        self.logger = get_logger()
        try:
            self.motors = microMX1508(motor1_pins = motor_a, motor2_pins = motor_b, accel_step=200, max_duty=500)
        except Exception as e:
            self.logger.info(f"ERROR Motors not started: {e}")
            sys.exit(1)

    def _turn_speed(self, abs_diff):
        if self.tolerance_heading < abs_diff <= self.tolerance_heading * 2:
            return 0
        elif self.tolerance_heading * 2 < abs_diff <= self.tolerance_heading * 8:
            return 1
        elif self.tolerance_heading * 8 < abs_diff <= self.tolerance_heading * 15:
            return 2
        else:
            return 3

    def move(self, current_heading, target_heading, stop):
        # Stop moving.
        if stop:
            self.status = "S"
            self.motors.stop()
            self.motors.update()
            return

        # Normalize headings to 0-360 range
        actual_h = int(current_heading % 360)
        target_h = int(target_heading % 360)
        diff = target_h - actual_h

        # Normalize the <0 ; 360> range to <-180 ; 180> range.
        if diff > 180:
            diff -= 360
        elif diff < -180:
            diff += 360

        abs_diff = abs(diff)

        # If the absolute value is withing acceptable margin, move forward.
        if abs_diff <= self.tolerance_heading:
            if self.debug_print:
                self.logger.info(f"forward {actual_h} {target_h}")
            self.status = "F"
            self.motors.forward()
            self.motors.update()
            return

        # Determine movement direction based on the sign.
        turn_speed = self._turn_speed(abs_diff)
        if diff > 0:
            if self.debug_print:
                self.logger.info(f"right {actual_h} {target_h} {turn_speed}")
            self.status = "R"
            self.motors.turn_right(turn_speed)
            self.motors.update()

        else:
            if self.debug_print:
                self.logger.info(f"left {actual_h} {target_h} {turn_speed}")
            self.status = "L"
            self.motors.turn_left(turn_speed)
            self.motors.update()


class Navigation:
    CENTIMETERS_PER_DEGREE_LAT_PRECISE = Precise("11113292")
    DEG_TO_RAD_PRECISE = Precise("0.017453292519943295")
    HALF_PRECISE = Precise("0.5")

    def __init__(self, i2c: I2C) -> None:
        self.compass = None
        self.logger = get_logger()
        try:
            self.compass = MinIMU9v6(i2c, calibrate=False)
        except Exception as e:
            self.logger.info(f"ERROR Compass not started: {e}")
            sys.exit(1)

    def calculate_distance_bearing(self, lon1_str, lat1_str, lon2_str, lat2_str):
        """
        Calculate distance (cm) and bearing (degrees) between two GNSS points.
        - Integer-only math,
        - Get RTK precision on 32bit platforms,
        - Optimised for speed,
        - Avoids overflow.

        Parameters:
        lon1_str, lat1_str:
            Point A coordinates as strings (e.g. '19.411551123387607', '51.70590960868671')
        lon2_str, lat2_str:
            Point B coordinates as strings (e.g. '19.411551123388000', '51.70590960868700')

        Returns:
            tuple: (distance_cm, bearing, heading)
                   distance_cm: distance in centimeters
                   bearing: bearing (e.g.17.00°)
                   heading: heading read from compass (e.g.10.00°)
        """
        lon1 = Precise(lon1_str)
        lat1 = Precise(lat1_str)
        lon2 = Precise(lon2_str)
        lat2 = Precise(lat2_str)

        lat1_rad = lat1 * Navigation.DEG_TO_RAD_PRECISE
        lat2_rad = lat2 * Navigation.DEG_TO_RAD_PRECISE
        delta_lat = lat2 - lat1
        delta_lon = lon2 - lon1

        # Meters per degree at average latitude (flat Earth approximation).
        lat_avg_rad = (lat1_rad + lat2_rad) * Navigation.HALF_PRECISE
        centimeters_per_deg_lat = Navigation.CENTIMETERS_PER_DEGREE_LAT_PRECISE
        centimeters_per_deg_lon = Navigation.CENTIMETERS_PER_DEGREE_LAT_PRECISE * Precise.cos(lat_avg_rad)

        # Convert delta degrees to centimeters.
        dx = delta_lon * centimeters_per_deg_lon
        dy = delta_lat * centimeters_per_deg_lat

        # Calculate bearing (0° = North, 90° = East).
        bearing_rad = Precise.atan2(dx, dy)
        bearing = round((float(bearing_rad.value_str) * 57.29578 + 360) % 360, 1)  # 180 / math.pi

        # Calculate distance using Pythagorean theorem (flat earth assumption).
        distance_cm = round(float(Precise.sqrt(dx * dx + dy * dy).value_str), 1)
        return distance_cm, bearing, self.compass.get_tilt_compensated_heading()
