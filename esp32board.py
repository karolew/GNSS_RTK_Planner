import time

import network
from machine import Pin, Timer

from logger import get_logger

try:
    import ubinascii as ubin
except:
    import binascii as ubin


class ErrorIndicator:
    def __init__(self, led_pin=2):
        self.led = Pin(led_pin, Pin.OUT)
        self.timer = Timer(0)
        self.is_blinking = False
        self.led.off()

    def start_blinking(self):
        if not self.is_blinking:
            self.is_blinking = True
            self.timer.init(period=100, mode=Timer.PERIODIC, callback=self._toggle_led)

    def stop_blinking(self):
        if self.is_blinking:
            self.is_blinking = False
            self.timer.deinit()
            self.led.off()

    def _toggle_led(self, t):
        self.led.value(not self.led.value())


# ErrorIndicator instance must be present.
error_indicator_led = ErrorIndicator()


class ErrorHandler:
    def __init__(self, stop_on_success=True):
        self.stop_on_success = stop_on_success

    def __enter__(self):
        error_indicator_led.start_blinking()
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback):
        if exc_type is None and self.stop_on_success:
            # No exception - stop blinking
            error_indicator_led.stop_blinking()
        elif exc_type is not None:
            # Exception occurred - keep blinking
            pass
        return False  # Don't suppress exception


class WLAN:
    def __init__(self, ssid: str, password: str ):
        self.ssid = ssid
        self.password = password
        self.sta_if = network.WLAN(network.STA_IF)
        self.logger = get_logger()

    def connect(self):
        timeout_s = 20
        time_attempt = time.time()
        error_indicator_led.start_blinking()
        if not self.sta_if.isconnected():
            self.logger.info("Connecting to WiFi...")
            self.sta_if.active(True)
            if not self.sta_if.isconnected():
                self.sta_if.connect(self.ssid, self.password)
            while not self.sta_if.isconnected():
                time.sleep(1)
                if time_attempt + timeout_s < time.time():
                    self.logger.info(f"Unable to connet WiFi network after {timeout_s} [s]. Retry.")
            self.logger.info(f"WiFi connected. Network config: {self.sta_if.ifconfig()}")
            error_indicator_led.stop_blinking()
        time.sleep(1)

    def check(self):
        if not self.sta_if.isconnected():
            self.connect()

    def get_mac(self):
        mymac = ""
        if self.sta_if.isconnected():
            mac_raw = self.sta_if.config("mac")
            mymac = ubin.hexlify(mac_raw).decode()
        return mymac
