import math

from machine import I2C

from microGY271.gy271compass import QMC5883L
from microMX1508.microMX1508 import microMX1508
from microNMEA.microNMEA import Precise


class Navigation:
    """
    Calculate distances and angles between GPS points with centimeter-level precision for small areas.
    It uses only the fractional parts therefore it avoids some of the complexities of full GPS
    coordinate conversions while maintaining precision at short distances.
    !!! This solution do not support points that cross integer degree boundaries !!!
    """

    def __init__(self, i2c: I2C,  direction_threshold: int = 5) -> None:
        self.meters_per_lat_degree = 111000
        self.meters_per_lon_degree_base = 111320
        self.direction_threshold = direction_threshold

        # Compass.
        self.compass = None
        try:
            self.compass = QMC5883L(i2c, corrections={"x_offset": 162, "x_scale": 1.04, "y_offset": -211, "y_scale": 0.97})
        except Exception as e:
            print(f"ERROR Compass not started: {e}")

        # Motors.
        self.max_speed_percent = 30     # range 0 - 100 %
        self.motors = None
        self.motors_status = "stop"
        try:
            self.motors = microMX1508((27, 14), (12, 13), accel_rate=5)
        except Exception as e:
            print(f"ERROR Motors not started: {e}")

    def meters_per_lon_degree(self, latitude: float) -> float:
        return self.meters_per_lon_degree_base * math.cos(math.radians(latitude))

    def extract_fractional(self, coord: tuple[str, str]) -> tuple[int, int]:
        lon, lat = coord
        lon_frac = Precise(lon).decimal_part
        lat_frac = Precise(lat).decimal_part
        return int(lon_frac[:Precise.decimal_places]), int(lat_frac[:Precise.decimal_places])

    def _calculate_delta(self, point_a: tuple[str, str], point_b: tuple[str, str]) -> tuple[float, float]:
        a_frac = self.extract_fractional(point_a)
        b_frac = self.extract_fractional(point_b)
        # Calculate differences in fractional parts.
        delta_lon = (b_frac[0] - a_frac[0]) / Precise.multiplier
        delta_lat = (b_frac[1] - a_frac[1]) / Precise.multiplier
        # Convert to meters (approximately).
        dx = delta_lon * self.meters_per_lon_degree(float(point_a[1]))
        dy = delta_lat * self.meters_per_lat_degree
        return dx, dy

    def distance(self, dx: float, dy: float) -> int:
        # Calculate Euclidean distance in cm.
        return round(math.sqrt(dx ** 2 + dy ** 2) * 100)

    def bearing(self, dx: float, dy: float) -> float:
        # Calculate angle in radians.
        angle_rad = math.atan2(dx, dy)
        # Convert to degrees (0-360).
        angle_deg = (angle_rad * 180 / math.pi) % 360
        return angle_deg

    def navigate_to_target(self, point_a: tuple[str, str], point_b: tuple[str, str], compass_heading: int) -> tuple:
        # Calculate the bearing to the target
        dx, dy = self._calculate_delta(point_a, point_b)
        target_bearing = self.bearing(dx, dy)
        target_distance = self.distance(dx, dy)
        # Calculate the difference between compass heading and target bearing
        angle_diff = (target_bearing - compass_heading) % 360
        # Determine the shortest angle and direction
        if angle_diff > 180:
            angle_diff = 360 - angle_diff
            direction = "left"
        else:
            direction = "right"
        # If angle_diff is very small or very large, we might be pointing
        # directly at or directly away from the target
        if angle_diff <= self.direction_threshold or angle_diff >= (360 - self.direction_threshold):
            on_target = True
        else:
            on_target = False
        # Ensure angle_diff is in the range 0-180
        if angle_diff > 180:
            angle_diff = 360 - angle_diff
        print(direction, angle_diff, compass_heading, target_distance)
        return "on_target" if on_target else direction, on_target, angle_diff, target_distance

    def turn_right(self):
        if self.motors_status == "right":
            pass
        elif self.motors_status != "stop":
            self.stop()
        else:
            self.motors.set_motor1(self.max_speed_percent)
            self.motors.set_motor2(-self.max_speed_percent)
            self.motors_status = "right"

    def turn_left(self):
        if self.motors_status == "left":
            pass
        elif self.motors_status != "stop":
            self.stop()
        else:
            self.motors.set_motor1(-self.max_speed_percent)
            self.motors.set_motor2(self.max_speed_percent)
            self.motors_status = "left"

    def forward(self):
        if self.motors_status == "forward":
            pass
        elif self.motors_status != "stop":
            self.stop()
        else:
            self.motors.set_motor1(self.max_speed_percent)
            self.motors.set_motor2(self.max_speed_percent)
            self.motors_status = "forward"

    def stop(self):
        if self.motors_status == "stop":
            pass
        else:
            self.motors.stop()
            self.motors_status = "stop"


if __name__ == "__main__":
    nav = Navigation()
    print(nav.navigate_to_target(["19.422820984529064", "51.77965793741643"],
                                 ["19.42282015391812", "51.779658443248195"],
                                 45))
