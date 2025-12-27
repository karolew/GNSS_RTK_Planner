import json

from machine import Pin

import logger
from esp32board import WLAN

# --------------------------------------------------
# Logger init.
# --------------------------------------------------
logger = logger.init_logger("rover.log", max_size=20480, use_file=True)

#logger.to_console()
logger.to_file()


# --------------------------------------------------
# Disable pins responsible for motor controlling.
# --------------------------------------------------
for gpio_no in (12, 13, 14, 27):
    p = Pin(gpio_no, Pin.OUT)
    p.init(pull=Pin.PULL_DOWN)
    p.off()
    logger.info(f"Set {gpio_no} to 0")


# --------------------------------------------------
# Load configuration.
# --------------------------------------------------
with open("config.json") as cfgf:
    config = json.load(cfgf)


# --------------------------------------------------
# Prepare WLAN.
# --------------------------------------------------
wlan = WLAN(config["wifi"]["ssid"],
            config["wifi"]["password"])
wlan.connect()


# --------------------------------------------------
# Run webrepl for debugging.
# --------------------------------------------------
try:
    import webrepl
    webrepl.start()
except:
    pass