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
        nav = Navigation(i2c)
    except Exception as e:
        print(f"ERROR Navigation not started: {e}")

    # RTK Planner.
    rtk_planner = RTKPlanner(config["server"]["url"], wlan.get_mac())

    # Rover must be registered in RTK planner first.
    rtk_planner.register()

    # Main loop.
    check_updates_s = time.time()   # interval for trail pull.
    previous_coordinates = (0, 0)   # To track coordinate changes.

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
                    previous_coordinates = micro_nmea.lat, micro_nmea.lon
            
            # HTTP pull trails every 5 seconds.
            if time.time() - check_updates_s > 5:
                rtk_planner.get_trails()
                check_updates_s = time.time()

            # Navigation part.
            if nav.motors:
                nav.motors.update()     # Must be here to update stop
                if rtk_planner.trail_points and nav.compass:
                    compass_heading = nav.compass.get_heading()
                    if compass_heading:
                        nav_status = nav.navigate_to_target((micro_nmea.lon, micro_nmea.lat),
                                                            rtk_planner.trail_points[0],
                                                            compass_heading)
                        if nav_status[3] <= 50:
                            # If we are on the target point +-5cm, mark as ready.
                            # Remove current coordinates from the trail.
                            print("POINT OK ---------------------------------------------", rtk_planner.trail_points[0])
                            rtk_planner.trail_points.pop(0)
                            nav.motors.move_stop()
                        else:
                            current_heading = compass_heading % 360
                            diff = abs(current_heading - nav_status[2])
                            clockwise_diff = (nav_status[2] - current_heading) % 360
                            counter_clockwise_diff = (current_heading - nav_status[2]) % 360

                            if diff <= nav.direction_threshold or (360 - diff) <= nav.direction_threshold:
                                nav.motors.forward()
                            elif clockwise_diff < counter_clockwise_diff:
                                turn_level = abs(clockwise_diff - nav.direction_threshold)
                                if turn_level <= 10:
                                    nav.motors.turn_right(0)
                                elif 10 < turn_level <= 25:
                                    nav.motors.turn_right(1)
                                elif 25 < turn_level <= 45:
                                    nav.motors.turn_right(2)
                                else:
                                    nav.motors.turn_right(3)
                            elif clockwise_diff >= counter_clockwise_diff:
                                turn_level = abs(counter_clockwise_diff - nav.direction_threshold)
                                if turn_level <= 10:
                                    nav.motors.turn_left(0)
                                elif 10 < turn_level <= 25:
                                    nav.motors.turn_left(1)
                                elif 25 < turn_level <= 45:
                                    nav.motors.turn_left(2)
                                else:
                                    nav.motors.turn_left(3)
                            else:
                                print("Stop", *nav_status, compass_heading)
                                nav.motors.move_stop()

        except Exception as e:
            print(f"Main loop error: {e}")


if __name__ == "__main__":
    main()
