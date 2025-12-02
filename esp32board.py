import network
from logger import get_logger
import time

try:
    import ubinascii as ubin
except:
    import binascii as ubin


class WLAN:
    def __init__(self, ssid: str, password: str ):
        self.ssid = ssid
        self.password = password
        self.sta_if = network.WLAN(network.STA_IF)
        self.logger = get_logger()

    def connect(self):
        timeout_s = 20
        time_attempt = time.time()
        if not self.sta_if.isconnected():
            self.logger.info("Connecting to WiFi...")
            self.sta_if.active(True)
            self.sta_if.connect(self.ssid, self.password)
            while not self.sta_if.isconnected():
                time.sleep(1)
                if time_attempt + timeout_s < time.time():
                    self.logger.info(f"Unable to connet WiFi network after {timeout_s} [s]. Retry.")
            self.logger.info("WiFi connected. Network config:", self.sta_if.ifconfig())
        time.sleep(1)

    def check(self):
        if not self.sta_if.isconnected():
            self.connect()

    def get_mac(self):
        if self.sta_if.isconnected():
            mac_raw = self.sta_if.config("mac")
            mymac = ubin.hexlify(mac_raw).decode()
            return mymac
