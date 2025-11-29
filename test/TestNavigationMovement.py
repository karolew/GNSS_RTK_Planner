import unittest
import sys
import io
from contextlib import redirect_stdout, redirect_stderr
from unittest.mock import MagicMock

# Mock MicroPython modules before importing Movement
sys.modules['machine'] = MagicMock()
sys.modules['microMX1508'] = MagicMock()
sys.modules['microMX1508.microMX1508'] = MagicMock()
sys.modules['microIMU9v6.imu9v6'] = MagicMock()
sys.modules['microNMEA.microNMEA'] = MagicMock()
from navigation import Movement


class TestMovementMove(unittest.TestCase):
    """Test suite for the Movement.move method"""

    def setUp(self):
        """Set up test fixtures before each test method"""
        self.movement = Movement()

    def test_turning(self):
        test_data = [
            # expected direction, current, target

            # forward equal
            ( "forward", 0, 0),
            ( "forward", 33, 33),
            ( "forward", 359, 359),
            ( "forward", 350, 350),

            # forward difference below threshold
            ( "forward", 0, 1),
            ( "forward", 1, 0),
            ( "forward", 0, 359),
            ( "forward", 359, 0),
            ( "forward", 359, 355),
            ( "forward", 355, 359),
            ( "forward", 50, 55),
            ( "forward", 55, 50),
            ( "forward", 180, 177),
            ( "forward", 177, 180),
            ( "forward", 179, 182),

            # right
            ( "right", 0, 6),
            ( "right", 354, 0),
            ( "right", 353, 359),
            ( "right", 359, 5),
            ( "right", 178, 184),
            ( "right", 180, 300),

            # left
            ("left", 6, 0),
            ("left", 0, 354),
            ("left", 359, 353),
            ("left", 5, 359),
            ("left", 184, 178),
            ("left", 300, 180),
        ]
        for test_no, td in enumerate(test_data, start=1):
            capture_stream = io.StringIO()
            with redirect_stdout(capture_stream), redirect_stderr(capture_stream):
                self.movement.move(td[1], td[2], False)
            expected = " ".join(map(str, td))
            actual = capture_stream.getvalue().replace("\n", "")
            with self.subTest():
                self.assertIn(expected, actual,
                              f"FAILED Test {test_no} Expected {expected}, actual: {actual}")
                print(f"PASSED Test {test_no} Expected {expected}, actual: {actual}")
