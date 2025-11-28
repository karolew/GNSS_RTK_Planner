import time

import network
import time

try:
    import ubinascii as ubin
except:
    import binascii as ubin


class WLAN:
    def __init__(self, ssid: str, password: str):
        self.ssid = ssid
        self.password = password
        self.sta_if = network.WLAN(network.STA_IF)

    def connect(self):
        timeout_s = 20
        time_attempt = time.time()
        if not self.sta_if.isconnected():
            print("Connecting to WiFi...")
            self.sta_if.active(True)
            self.sta_if.connect(self.ssid, self.password)
            while not self.sta_if.isconnected():
                time.sleep(1)
                if time_attempt + timeout_s < time.time():
                    print(f"Unable to connet WiFi network after {timeout_s} [s]. Retry.")
            print("WiFi connected. Network config:", self.sta_if.ifconfig())
        time.sleep(1)

    def check(self):
        if not self.sta_if.isconnected():
            self.connect()

    def get_mac(self):
        if self.sta_if.isconnected():
            mac_raw = self.sta_if.config("mac")
            mymac = ubin.hexlify(mac_raw).decode()
            return mymac

class Logger:
    def __init__(self, file_path_to_log: str) -> None:
        self.file_path_to_log = file_path_to_log

    def _get_timestamp(self) -> str:
        year, month, day, _, hour, minute, second, _ = time.localtime()
        return "{:04d}-{:02d}-{:02d} {:02d}:{:02d}:{:02d}".format(year, month, day, hour, minute, second)

    def info(self, message: str) -> None:
        with open(self.file_path_to_log, "a") as f:
            f.write(self._get_timestamp() + ": " + str(message) + "\n")
