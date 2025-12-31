import unittest
import sys
from unittest.mock import MagicMock, Mock, patch

# Mock MicroPython modules before importing Movement.
sys.modules['machine'] = MagicMock()
sys.modules['microMX1508'] = MagicMock()
sys.modules['microMX1508.microMX1508'] = MagicMock()
sys.modules['microIMU9v6'] = MagicMock()
sys.modules['microIMU9v6.imu9v6'] = MagicMock()
sys.modules['microNMEA'] = MagicMock()
sys.modules['microNMEA.microNMEA'] = MagicMock()
sys.modules['logger'] = MagicMock()

from navigation import Movement


class TestMovementMove(unittest.TestCase):
    """Test suite for the Movement.move method"""

    def setUp(self):
        # Mock the logger before creating Movement instance
        self.logger_patcher = patch('navigation.get_logger')
        self.mock_get_logger = self.logger_patcher.start()
        self.mock_logger = Mock()
        self.mock_get_logger.return_value = self.mock_logger

        # Mock microMX1508 to avoid motor initialization
        self.motor_patcher = patch('navigation.microMX1508')
        self.mock_motor_class = self.motor_patcher.start()
        self.mock_motors = Mock()
        self.mock_motor_class.return_value = self.mock_motors

        # Create Movement instance
        self.movement = Movement()

    def tearDown(self):
        self.logger_patcher.stop()
        self.motor_patcher.stop()

    def test_turning(self):
        test_data = [
            # expected direction, current, target

            # forward equal
            ("forward", 0, 0),
            ("forward", 33, 33),
            ("forward", 359, 359),
            ("forward", 350, 350),

            # forward difference below threshold
            ("forward", 0, 1),
            ("forward", 1, 0),
            ("forward", 0, 359),
            ("forward", 359, 0),
            ("forward", 359, 355),
            ("forward", 355, 359),
            ("forward", 50, 55),
            ("forward", 55, 50),
            ("forward", 180, 177),
            ("forward", 177, 180),
            ("forward", 179, 182),

            # right
            ("right", 0, 6),
            ("right", 354, 0),
            ("right", 353, 359),
            ("right", 359, 5),
            ("right", 178, 184),
            ("right", 180, 300),

            # left
            ("left", 6, 0),
            ("left", 0, 354),
            ("left", 359, 353),
            ("left", 5, 359),
            ("left", 184, 178),
            ("left", 300, 180),
        ]

        for test_no, td in enumerate(test_data, start=1):
            expected_direction, current, target = td

            self.mock_logger.info.reset_mock()
            self.mock_motors.reset_mock()

            self.movement.move(current, target, False)
            logged_message = self.mock_logger.info.call_args[0][0]
            with self.subTest(test_no=test_no, current=current, target=target):
                self.assertIn(expected_direction, logged_message.lower(),
                              f"Test {test_no}: Expected '{expected_direction}' in log message. "
                              f"Current: {current}, Target: {target}, "
                              f"Logged: '{logged_message}'")
                print(f"PASSED Test {test_no}: Expected '{expected_direction}', "
                      f"Current: {current}, Target: {target}, "
                      f"Logged: '{logged_message}'")


if __name__ == '__main__':
    unittest.main()
