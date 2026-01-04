import json
import time

import urequests

from esp32board import error_indicator_led
from logger import get_logger


class RTKPlanner:
    # Data structure to send to RTK Planner.
    gps_data = {
        "mac": None,
        "fix_status": "Unknowsn",
        "latitude": None,
        "longitude": None,
        "lat_raw": None,
        "lon_raw": None,
        "speed": None,
        "course": None,
        "time_utc": None,
        "last_update": None,
        "sv": None,
        "su": None
    }

    def __init__(self, host: str, port: str, mac):
        self.url = f"http://{host}:{port}"
        self.mac = mac
        self.trail_points = []
        self.logger = get_logger()

    def register(self):
        error_indicator_led.start_blinking()
        while True:
            try:
                response = urequests.post(self.url + "/rover/register",
                                          headers={"Content-Type": "application/json"},
                                          json=json.dumps({"mac": self.mac}),
                                          timeout=1)
                response_code = response.status_code
                response.close()
                if response_code == 200:
                    self.logger.info("Rover is registered.")
                    break
                else:
                    self.logger.info("Rover is NOT registered. Wait for confirmation.")
                error_indicator_led.stop_blinking()
            except Exception as e:
                self.logger.info(f"Failed to send mac {self.mac}: {e}")
            time.sleep(2)

    def get_trails(self):
        try:
            # Make HTTP GET request to Flask server
            response = urequests.get(self.url + "/trail/upload")
            if response.status_code == 200:
                data = response.json()
                if data.get('mac') == self.mac:
                    self.trail_points = json.loads(data.get('trail_points').replace("'", "\""))
                    self.logger.info(f"Received new trails: {self.trail_points}.")

            response.close()
        except Exception as e:
            self.logger.info(f"Error getting trails {e}")

    def send_gnss_update(self, nmea_data):
        self.gps_data["latitude"] = nmea_data.lat
        self.gps_data["longitude"] = nmea_data.lon
        self.gps_data["fix_status"] = nmea_data.quality
        self.gps_data["speed"] = nmea_data.speed
        self.gps_data["course"] = nmea_data.course
        self.gps_data["time_utc"] = nmea_data.time
        self.gps_data["sv"] = nmea_data.gsv_data
        self.gps_data["su"] = nmea_data.satellites_used
        self.gps_data["mac"] = self.mac
        try:
            response = urequests.post(self.url + "/rover/update_gps",
                                      headers={"Content-Type": "application/json"},
                                      json=json.dumps(self.gps_data),
                                      timeout=1)
            response.close()
        except Exception as e:
            self.logger.info(f"Failed to send data: {e}")
