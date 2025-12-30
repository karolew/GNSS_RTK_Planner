import sys
import unittest
from unittest.mock import Mock, MagicMock, patch


class MockPrecise:
    def __init__(self, coord_str):
        parts = coord_str.split('.')
        self.whole_part_with_sign = parts[0]
        # Pad decimal part to 6 digits with zeros.
        if len(parts) > 1:
            self.decimal_part = parts[1][:10].ljust(10, '0')
        else:
            self.decimal_part = '0000000000'

sys.modules['machine'] = MagicMock()
sys.modules['logger'] = MagicMock()
sys.modules['microIMU9v6'] = MagicMock()
sys.modules['microIMU9v6.imu9v6'] = MagicMock()
sys.modules['microMX1508'] = MagicMock()
sys.modules['microMX1508.microMX1508'] = MagicMock()

# Create mock module with MockPrecise.
mock_microNMEA = MagicMock()
mock_microNMEA_microNMEA = MagicMock()
mock_microNMEA_microNMEA.Precise = MockPrecise
sys.modules['microNMEA'] = mock_microNMEA
sys.modules['microNMEA.microNMEA'] = mock_microNMEA_microNMEA

from navigation import Navigation


class TestNavigation(unittest.TestCase):
    def setUp(self):
        # Mock the logger.
        self.logger_patcher = patch('navigation.get_logger')
        self.mock_get_logger = self.logger_patcher.start()
        self.mock_logger = Mock()
        self.mock_get_logger.return_value = self.mock_logger
        # Mock the I2C.
        self.mock_i2c = Mock()
        # Mock MinIMU9v6 constructor to avoid initialization issues.
        with patch('navigation.MinIMU9v6') as mock_imu_class:
            mock_compass = Mock()
            mock_compass.get_tilt_compensated_heading = Mock(return_value=90)
            mock_imu_class.return_value = mock_compass
            self.nav = Navigation(self.mock_i2c)

    def tearDown(self):
        self.logger_patcher.stop()

    def test_same_location(self):
        lon = "19.411551"
        lat = "51.705909"
        dist_cm, bearing, heading = self.nav.calculate_distance_bearing(lon, lat, lon, lat)
        self.assertEqual(dist_cm, 0, "Distance should be 0 for identical points")
        self.assertEqual(bearing, 0, "Bearing should be 0 for identical points")

    def test_northward_movement(self):
        lon1 = "19.411551"
        lat1 = "51.705909"
        lon2 = "19.411551"
        lat2 = "51.706909"  # ~1000 microdegrees north.
        dist_cm, bearing, heading = self.nav.calculate_distance_bearing(lon1, lat1, lon2, lat2)
        self.assertAlmostEqual(dist_cm, 11132, delta=100,
                               msg="Distance for 0.001 degree north should be ~111 meters")
        self.assertAlmostEqual(bearing, 0, delta=5,
                               msg="Bearing for northward movement should be ~0 degrees")

    def test_eastward_movement(self):
        lon1 = "19.411551"
        lat1 = "51.705909"
        lon2 = "19.412551"  # 1000 microdegrees east.
        lat2 = "51.705909"
        dist_cm, bearing, heading = self.nav.calculate_distance_bearing(lon1, lat1, lon2, lat2)
        self.assertGreater(dist_cm, 0, "Distance should be positive")
        self.assertAlmostEqual(bearing, 90, delta=5,
                               msg="Bearing for eastward movement should be ~90 degrees")

    def test_southward_movement(self):
        lon1 = "19.411551"
        lat1 = "51.706909"
        lon2 = "19.411551"
        lat2 = "51.705909"  # 1000 microdegrees south.
        dist_cm, bearing, heading = self.nav.calculate_distance_bearing(lon1, lat1, lon2, lat2)
        self.assertAlmostEqual(dist_cm, 11132, delta=100,
                               msg="Distance for 0.001 degree south should be ~111 meters")
        self.assertAlmostEqual(bearing, 180, delta=5,
                               msg="Bearing for southward movement should be ~180 degrees")

    def test_westward_movement(self):
        lon1 = "19.412551"
        lat1 = "51.705909"
        lon2 = "19.411551"  # 1000 microdegrees west.
        lat2 = "51.705909"
        dist_cm, bearing, heading = self.nav.calculate_distance_bearing(lon1, lat1, lon2, lat2)
        self.assertGreater(dist_cm, 0, "Distance should be positive")
        self.assertAlmostEqual(bearing, 270, delta=5,
                               msg="Bearing for westward movement should be ~270 degrees")

    def test_diagonal_movement(self):
        lon1 = "19.411551"
        lat1 = "51.705909"
        lon2 = "19.412551"  # East.
        lat2 = "51.706909"  # .
        dist_cm, bearing, heading = self.nav.calculate_distance_bearing(lon1, lat1, lon2, lat2)
        self.assertGreater(dist_cm, 0, "Distance should be positive")
        self.assertGreater(bearing, 0, "Bearing should be > 0 for NE movement")
        self.assertLess(bearing, 90, "Bearing should be < 90 for NE movement")

    def test_negative_coordinates(self):
        lon1 = "-122.419416"
        lat1 = "37.774929"
        lon2 = "-122.419416"
        lat2 = "37.775929"  # North.
        dist_cm, bearing, heading = self.nav.calculate_distance_bearing(lon1, lat1, lon2, lat2)
        self.assertGreater(dist_cm, 0, "Distance should be positive with negative coords")
        self.assertAlmostEqual(bearing, 0, delta=5,
                               msg="Bearing north should still be ~0 with negative coords")

    def test_small_distance(self):
        lon1 = "19.411551123387607"
        lat1 = "51.705909608686710"
        lon2 = "19.411551123388000"
        lat2 = "51.705909608687000"
        dist_cm, bearing, heading = self.nav.calculate_distance_bearing(lon1, lat1, lon2, lat2)
        self.assertGreaterEqual(dist_cm, 0, "Distance should be non-negative")


if __name__ == '__main__':
    unittest.main()