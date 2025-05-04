import json
import time

from machine import I2C, Pin

from esp32board import WLAN
from microNMEA.microNMEA import MicroNMEA
from navigation import Navigation
from ntripclient import NTRIPClient
from px11222r import PX1122RUART
from rtkplanner import RTKPlanner

try:
    import ubinascii as ubin
except:
    import binascii as ubin


def main():
    # Load configuration.
    with open("config.json") as cfgf:
        config = json.load(cfgf)

    # WLAN.
    wlan = WLAN(config["wifi"]["ssid"],
                config["wifi"]["password"])
    wlan.connect()

    # UART.
    gps_uart = PX1122RUART(uart_id=2)

    # NMEA decoder.
    micro_nmea = MicroNMEA(units=1)

    # NTRIP server.
    ntrip_client = NTRIPClient(config["ntrip"]["host"],
                               config["ntrip"]["port"],
                               config["ntrip"]["mountpoint"],
                               config["ntrip"]["user"],
                               config["ntrip"]["password"])
    ntrip_client.connect()

    # Navigation.
    nav = None
    try:
        i2c = I2C(0, scl=Pin(22), sda=Pin(21), freq=100000)
        nav = Navigation(i2c, 20)
    except Exception as e:
        print(f"ERROR Navigation not started: {e}")

    # RTK Planner.
    rtk_planner = RTKPlanner(config["server"]["url"], wlan.get_mac())

    # Rover must be registered in RTK planner first.
    rtk_planner.register()

    # Main loop.
    check_updates_s = time.time()   # interval for trail pull.
    previous_coordinates = (0, 0)   # To track coordinate changes.
    target_coord = None
    while True:
        try:
            # Check WLAN status.
            wlan.check()

            # Receive NTRIP data from configured service.
            ntrip_data = ntrip_client.read_data()

            # Resend NTRIP data to GNSS rover.
            gps_uart.send_data(ntrip_data)

            # Receive data from GNSS rover. Check data is correct.
            sentence = gps_uart.process_received_data()

            if sentence:
                # Decode NMEA data.
                micro_nmea.parse(sentence)

                # Send data to RTK Planner server.
                if (micro_nmea.lat, micro_nmea.lon) != previous_coordinates:
                    rtk_planner.send_gnss_update(micro_nmea)
            
            # HTTP pull trails every 5 seconds.
            if time.time() - check_updates_s > 5:
                rtk_planner.get_trails()
                check_updates_s = time.time()

            # Navigation part.
            if rtk_planner.trail_points and nav.compass and nav.motors:
                compass_heading = nav.compass.get_heading()
                if not target_coord:
                    target_coord = (micro_nmea.lon, micro_nmea.lat)
                nav_status = nav.navigate_to_target((micro_nmea.lon, micro_nmea.lat), target_coord, compass_heading)
                if nav_status[3] <= 5:
                    # If we are on the target point +-5cm, mark as ready.
                    # Get next element from the trail.
                    target_coord = rtk_planner.trail_points.pop(0)
                else:
                    if nav_status[0] == "left":
                        print("Skrecamy w lewo")
                    elif nav_status[0] == "right":
                        print("Skrecamy w prawo")
                    else:
                        print("Jedziemy prosto")
            else:
                # Navigation finished.
                target_coord = None

        except Exception as e:
            print(f"Main loop error: {e}")


if __name__ == "__main__":
    main()
