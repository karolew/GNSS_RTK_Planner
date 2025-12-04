import sys
from logger import get_logger
from machine import I2C

from microIMU9v6.imu9v6 import MinIMU9v6
from microMX1508.microMX1508 import microMX1508
from microNMEA.microNMEA import Precise


class Movement:
    def __init__(self, motor_a = (27, 14), motor_b = (12, 13), tolerance_heading = 5) -> None:
        self.tolerance_heading = tolerance_heading
        self.motors = None
        self.logger = get_logger()
        try:
            self.motors = microMX1508(motor1_pins = motor_a, motor2_pins = motor_b, accel_step=200, max_duty=512)
        except Exception as e:
            self.logger.info(f"ERROR Motors not started: {e}")
            sys.exit(1)

    def _turn_speed(self, abs_diff):
        if self.tolerance_heading < abs_diff <= 20:
            return 0
        elif 20 < abs_diff <= 50:
            return 1
        elif 50 < abs_diff <= 80:
            return 2
        else:
            return 3

    def move(self, current_heading, target_heading, stop):
        # Stop moving.
        if stop:
            self.motors.stop()
            self.motors.update()
            return

        # Normalize headings to 0-360 range
        actual_h = current_heading % 360
        target_h = target_heading % 360
        diff = target_h - actual_h

        # Normalize the <0 ; 360> range to <-180 ; 180> range.
        if diff > 180:
            diff -= 360
        elif diff < -180:
            diff += 360

        abs_diff = abs(diff)

        # If the absolute value is withing acceptable margin, move forward.
        if abs_diff <= self.tolerance_heading:
            self.logger.info('forward', actual_h, target_h)
            self.motors.forward()
            self.motors.update()
            return

        # Determine movement direction based on the sign.
        if diff > 0:
            self.logger.info('right', actual_h, target_h)
            self.motors.turn_right(self._turn_speed(abs_diff))
            self.motors.update()

        else:
            self.logger.info('left', actual_h, target_h)
            self.motors.turn_left(self._turn_speed(abs_diff))
            self.motors.update()


class Navigation:
    def __init__(self, i2c: I2C) -> None:
        self.compass = None
        self.logger = get_logger()
        try:
            self.compass = MinIMU9v6(i2c, calibrate=False)
        except Exception as e:
            self.logger.info(f"ERROR Compass not started: {e}")
            sys.exit(1)

    def isqrt(self, n):
        """Integer square root using Newton's method"""
        if n == 0:
            return 0
        x = n
        y = (x + 1) // 2
        while y < x:
            x = y
            y = (x + n // x) // 2
        return x

    def atan2_int(self, y, x):
        """
        Integer atan2 approximation returning angle in degrees * 100
        Input: y, x in any integer units
        Output: angle in degrees * 100 (0-36000 representing 0-360°)
        """
        if x == 0 and y == 0:
            return 0

        # Determine octant and calculate base angle
        abs_y = abs(y)
        abs_x = abs(x)

        # Calculate ratio and angle using polynomial approximation
        if abs_x > abs_y:
            # More horizontal
            ratio = (abs_y * 10000) // abs_x
            # atan(r) ≈ r - r³/3 + r⁵/5 (for small r, r in radians)
            # Convert to degrees: multiply by 180/π ≈ 5730/10000
            ratio_sq = (ratio * ratio) // 10000
            ratio_cu = (ratio_sq * ratio) // 10000
            angle = (ratio * 5730) // 10000 - (ratio_cu * 1910) // 10000

            if x > 0 and y >= 0:  # Q1
                return angle
            elif x < 0 and y >= 0:  # Q2
                return 18000 - angle
            elif x < 0 and y < 0:  # Q3
                return 18000 + angle
            else:  # Q4
                return 36000 - angle
        else:
            # More vertical
            ratio = (abs_x * 10000) // abs_y
            ratio_sq = (ratio * ratio) // 10000
            ratio_cu = (ratio_sq * ratio) // 10000
            angle = 9000 - ((ratio * 5730) // 10000 - (ratio_cu * 1910) // 10000)

            if x >= 0 and y > 0:  # Q1
                return angle
            elif x < 0 and y > 0:  # Q2
                return 18000 - angle
            elif x < 0 and y < 0:  # Q3
                return 18000 + angle
            else:  # Q4
                return 36000 - angle

    def cos_int(self, lat_microdeg):
        """
        Calculate cosine for latitude correction
        Input: latitude in microdegrees (degrees * 1000000)
        Output: cosine * 10000
        """
        # Convert to degrees * 100 for calculation
        deg = lat_microdeg // 10000

        # Normalize to 0-36000
        deg = deg % 36000
        if deg < 0:
            deg += 36000

        # Use symmetry to work in first quadrant (0-9000)
        if deg <= 9000:
            angle = deg
            sign = 1
        elif deg <= 18000:
            angle = 18000 - deg
            sign = -1
        elif deg <= 27000:
            angle = deg - 18000
            sign = -1
        else:
            angle = 36000 - deg
            sign = 1

        # Convert to radians * 10000: angle * π / 180
        # π / 180 ≈ 0.017453 ≈ 1745 / 100000
        rad_x10000 = (angle * 1745) // 1000

        # Taylor series: cos(x) ≈ 1 - x²/2 + x⁴/24
        # Working with 10000 as base unit
        rad_sq = (rad_x10000 * rad_x10000) // 10000
        rad_4 = (rad_sq * rad_sq) // 10000

        cos_val = 10000 - (rad_sq * 5000) // 10000 + (rad_4 * 417) // 10000

        return cos_val * sign

    def str_to_microdegrees(self, coord_str):
        """
        Convert coordinate string to microdegrees (degrees * 1,000,000)
        Handles up to 9 decimal places without using float
        Example: "49.951389" -> 49951389
        """
        p = Precise(coord_str)
        integer_part = p.whole_part_with_sign
        decimal_part = p.decimal_part[:6]
        sign = -1 if "-" == integer_part[0] else 1
        microdeg = int(integer_part) * 1000000 + sign * int(decimal_part)
        return microdeg

    def calculate_distance_bearing(self, lat1_str, lon1_str, lat2_str, lon2_str):
        """
        Calculate distance (cm) and bearing (degrees * 100) between two GNSS points.
        Integer-only math for ESP32 speed, avoids overflow.
        lat1_str, lon1_str: Point A coordinates as strings (e.g., "49.951389")
        lat2_str, lon2_str: Point B coordinates as strings (e.g., "49.951391")
        Returns:
            tuple: (distance_cm, bearing_deg_x100, heading_deg)
                   distance_cm: distance in centimeters
                   bearing_deg_x100: bearing * 100 (e.g., 1700 = 17.00°)
        """
        # Convert string coordinates to integers (microdegrees: degrees * 1,000,000)
        lat1 = self.str_to_microdegrees(lat1_str)
        lon1 = self.str_to_microdegrees(lon1_str)
        lat2 = self.str_to_microdegrees(lat2_str)
        lon2 = self.str_to_microdegrees(lon2_str)

        # Calculate differences in microdegrees
        dlat = lat2 - lat1
        dlon = lon2 - lon1

        # Average latitude for longitude correction
        lat_avg = (lat1 + lat2) // 2

        # Get cos(lat_avg), result is * 10000
        cos_lat = self.cos_int(lat_avg)

        # Earth's circumference / 360 = 111320 meters per degree
        # = 111.32 meters per 0.001 degree (millidegree)
        # = 0.11132 meters per microdegree
        # = 11.132 cm per microdegree

        # Calculate in millimeters to avoid overflow
        # 1 microdegree = 111.32 mm
        # Split the constant: 111.32 = 11132 / 100

        # y (north-south) in millimeters
        # Avoid overflow: (dlat * 11132) might overflow, so divide first
        y_mm = (dlat * 1113) // 10  # dlat * 111.3

        # x (east-west) in millimeters, corrected for latitude
        # x = dlon * cos(lat) * 111.32
        # cos_lat is * 10000, so divide by 10000
        # To avoid overflow: (dlon * cos_lat) might overflow
        # Rearrange: (dlon * 1113 * cos_lat) / (10 * 10000)
        x_mm = (dlon * cos_lat * 1113) // 100000

        # Calculate distance in millimeters
        dist_mm = self.isqrt(x_mm * x_mm + y_mm * y_mm)

        # Convert to centimeters (round to nearest)
        dist_cm = (dist_mm + 5) // 10

        # Calculate bearing using integer atan2
        bearing_x100 = self.atan2_int(x_mm, y_mm)

        # Ensure bearing is positive (0-36000)
        if bearing_x100 < 0:
            bearing_x100 += 36000

        return dist_cm, bearing_x100//100, self.compass.get_tilt_compensated_heading()
