"""
This is connector between objects defined in boot and their usage in main.
This is only to supress the IDE warnings.
"""


try:
    config
except NameError:
    config = None

try:
    logger
except NameError:
    logger = None

try:
    wlan
except NameError:
    wlan = None
