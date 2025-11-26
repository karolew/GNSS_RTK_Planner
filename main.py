import json
import time

from machine import I2C, Pin, Timer

from esp32board import WLAN
from microNMEA.microNMEA import MicroNMEA
from navigation import Navigation, Movement
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
    timer = Timer(0)
    compass_calibration = False
    compass_long_press_ms = 2000
    compass_calibration_led_status = Pin(23, Pin.OUT)
    compass_calibration_button = Pin(26, Pin.IN, Pin.PULL_UP)

    def compass_on_long_press(t):
        global compass_calibration
        if compass_calibration_button.value() == 0:
            compass_calibration = True

    def handle_interrupt_for_compass_calibration(pin) -> None:
        if pin.value() == 0:
            timer.init(period=compass_long_press_ms, mode=Timer.ONE_SHOT, callback=compass_on_long_press)
        else:
            timer.deinit()
    compass_calibration_button.irq(trigger=Pin.IRQ_FALLING, handler=handle_interrupt_for_compass_calibration)

    # Compass and driving motors.
    i2c = I2C(0, scl=Pin(22), sda=Pin(21), freq=100000)
    nav = Navigation(i2c)
    mov = Movement((27, 14), (12, 13), tolerance_heading = 5)


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
    previous_quality = ""
    target_threshold = 50  # TODO should be configurable from portal.

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
                if ((micro_nmea.lat, micro_nmea.lon) != previous_coordinates
                        or micro_nmea.quality != previous_quality):
                    rtk_planner.send_gnss_update(micro_nmea)
                    previous_coordinates = micro_nmea.lat, micro_nmea.lon
                    previous_quality = micro_nmea.quality
            
            # HTTP pull trails every 5 seconds.
            if time.time() - check_updates_s > check_updates_interval_s:
                rtk_planner.get_trails()
                check_updates_s = time.time()

            # Navigation part.
            # Calibrate compass if button is pressed.
            if compass_calibration:
                compass_calibration_led_status.value(1)
                nav.compass.calibrate_magnetometer()
                compass_calibration_led_status.value(0)
                compass_calibration = False

            if micro_nmea.quality not in ["SPS Fix", "RTK Fix", "RTK Float"]:
                print("No RTK fix")
                mov.move(-1, -1, True)
                continue

            if not rtk_planner.trail_points:
                mov.move(-1, -1, True)
                print("NO TRAIL")
                continue

            dist, target_heading, current_heading = nav.calculate_distance_bearing(*rtk_planner.trail_points[0], micro_nmea.lon, micro_nmea.lat)
            mov.move(current_heading, target_heading, False)
            print("POS", micro_nmea.lon, micro_nmea.lat, "MOVING to: ", rtk_planner.trail_points[0], dist, target_heading, current_heading)
            if dist <= target_threshold:
                print(f"TRAIL POIT REACHED: {rtk_planner.trail_points[0]}")
                rtk_planner.trail_points.pop(0)

        except Exception as e:
            print(f"Main loop error: {e}")
