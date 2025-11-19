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


if __name__ == "__main__":
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
    # Prepare UART to communicate with RTK module.
    # --------------------------------------------------
    gps_uart = PX1122RUART(uart_id=2)

    # --------------------------------------------------
    # Prepare NMEA decoder.
    # --------------------------------------------------
    micro_nmea = MicroNMEA(units=1)

    # --------------------------------------------------
    # Prepare NTRIP server.
    # --------------------------------------------------
    ntrip_client = NTRIPClient(config["ntrip"]["host"],
                               config["ntrip"]["port"],
                               config["ntrip"]["mountpoint"],
                               config["ntrip"]["user"],
                               config["ntrip"]["password"])
    ntrip_client.connect()

    # --------------------------------------------------
    # Prepare Compass and driving motors.
    # --------------------------------------------------

    # Button and led status for compass calibration.
    compas_calibration = False
    def handle_interrupt_for_compass_calibration(pin) -> None:
        global compas_calibration
        compas_calibration = True
    compass_calibration_led_status = Pin(23, Pin.OUT)
    compass_calibration_button = Pin(26, Pin.IN, Pin.PULL_UP)
    compass_calibration_button.irq(trigger=Pin.IRQ_FALLING, handler=handle_interrupt_for_compass_calibration)

    # Compass and driving motors.
    nav = None
    try:
        i2c = I2C(0, scl=Pin(22), sda=Pin(21), freq=100000)
        nav = Navigation(i2c)
    except Exception as e:
        print(f"ERROR Navigation not started: {e}")

    # --------------------------------------------------
    # RTK Planner.
    # --------------------------------------------------
    rtk_planner = RTKPlanner(config["server"]["host"], config["server"]["port"], wlan.get_mac())

    # Rover must be registered in RTK planner first.
    rtk_planner.register()

    # Main loop variables.
    check_updates_s = time.time()   # Timer for trail pull.
    check_updates_interval_s = 5    # Interval for trail pull.
    previous_coordinates = (0, 0)   # To track coordinate changes.
    target_threshold = 50           # TODO should be configurable from portal.

    # --------------------------------------------------
    #
    # Start main loop.
    #
    # --------------------------------------------------
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
            if time.time() - check_updates_s > check_updates_interval_s:
                rtk_planner.get_trails()
                check_updates_s = time.time()

            # Navigation part.
            # Calibrate compass if button is pressed.
            if nav.compass and compas_calibration:
                compass_calibration_led_status.value(1)
                nav.compass.calibrate_magnetometer()
                compass_calibration_led_status.value(0)
                compas_calibration = False

            # If motors are present do nothing.
            if nav.motors:
                # Must be here to update stop.
                nav.motors.update()

                # Check trail points are present and compass in working.
                # Stop motor if these conditions are not meet.
                if not rtk_planner.trail_points or not nav.compass:
                    print(nav.compass.get_tilt_compensated_heading())
                    nav.motors.stop()
                    continue

                # If compass heading calculation is incorrect or crashed skip it.
                compass_heading = nav.compass.get_tilt_compensated_heading()
                if not compass_heading:
                    continue

                nav_status = nav.navigate_to_target((micro_nmea.lon, micro_nmea.lat),
                                                    rtk_planner.trail_points[0],
                                                    compass_heading)
                if nav_status[3] <= target_threshold:
                    # If rover is on the target point +-target_threshold, mark as ready.
                    # Remove current coordinates from the trail.
                    nav.motors.move_stop()
                    print(f"TRAIL POIT REACHED: {rtk_planner.trail_points[0]}")
                    rtk_planner.trail_points.pop(0)
                else:
                    current_heading = compass_heading % 360
                    diff = abs(current_heading - nav_status[2])
                    clockwise_diff = (nav_status[2] - current_heading) % 360
                    counter_clockwise_diff = (current_heading - nav_status[2]) % 360
                    print(nav.compass.get_tilt_compensated_heading(), diff, clockwise_diff, counter_clockwise_diff)

                    if diff <= nav.direction_threshold or (360 - diff) <= nav.direction_threshold:
                        nav.motors.forward()
                        print("PROSTO")
                    elif clockwise_diff < counter_clockwise_diff:
                        turn_level = abs(clockwise_diff - nav.direction_threshold)
                        if turn_level <= 10:
                            nav.motors.turn_right(0)
                            print("PROSTO PRAWO 0")
                        elif 10 < turn_level <= 20:
                            nav.motors.turn_right(1)
                            print("PROSTO PRAWO 1")
                        elif 20 < turn_level <= 30:
                            nav.motors.turn_right(2)
                            print("PROSTO PRAWO 2")
                        else:
                            nav.motors.turn_right(3)
                            print("ZAWRACANIE PRAWO")
                    elif clockwise_diff >= counter_clockwise_diff:
                        turn_level = abs(counter_clockwise_diff - nav.direction_threshold)
                        if turn_level <= 10:
                            nav.motors.turn_left(0)
                            print("PROSTO LEWO 0")
                        elif 10 < turn_level <= 20:
                            nav.motors.turn_left(1)
                            print("PROSTO LEWO 1")
                        elif 20 < turn_level <= 30:
                            nav.motors.turn_left(2)
                            print("PROSTO LEWO 2")
                        else:
                            nav.motors.turn_left(3)
                            print("ZAWRACANIE LEWO")
                    else:
                        print("Stop", *nav_status, compass_heading)
                        nav.motors.move_stop()
                        print("STOP")

        except Exception as e:
            print(f"Main loop error: {e}")
