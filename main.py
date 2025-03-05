import json
import socket
import time

import network
import urequests
from machine import UART

from microNMEA.microNMEA import MicroNMEA

try:
    import ubinascii as ubin
except:
    import binascii as ubin


class UARTReceiver:
    def __init__(self, uart_id=2, baud_rate=115200, buffer_size=1024):
        self.uart = UART(uart_id, baudrate=baud_rate, rxbuf=buffer_size, txbuf=buffer_size)
        self.message_buffer = bytearray()
        self.receiving_message = False

    def send_data(self, data_to_send):
        if data_to_send:
            # Send NTRIP data to UART.
            self.uart.write(data_to_send)

    def process_received_data(self):
        if self.uart.any():  # Check if data available.
            try:
                # Read available bytes (non-blocking).
                data = self.uart.read()

                if data:
                    for byte in data:
                        if byte == ord("$"):
                            # Start of new message.
                            self.message_buffer = bytearray([byte])
                            self.receiving_message = True
                        elif self.receiving_message:
                            self.message_buffer.append(byte)
                            if byte == ord("\n"):
                                # Message complete.
                                message = bytes(self.message_buffer)
                                self.receiving_message = False
                                self.message_buffer = bytearray()
                                return message.decode("utf-8")[:-2]

                        # Protection against buffer overflow
                        if len(self.message_buffer) > 1024:
                            self.message_buffer = bytearray()
                            self.receiving_message = False
            except Exception as e:
                print(f"Error processing UART data: {e}")
                self.message_buffer = bytearray()
                self.receiving_message = False
        return None


class NTRIPClient:
    def __init__(self, host, port, mountpoint, username, password):
        self.host = host
        self.port = port
        self.mountpoint = mountpoint
        self.username = username
        self.password = password
        self.socket = None

    def connect(self):
        try:
            # Create socket connection
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.settimeout(10)
            self.socket.connect((self.host, self.port))

            # Prepare authentication string
            auth = ubin.b2a_base64(f"{self.username}:{self.password}".encode()).decode()

            # Create NTRIP request
            request = (
                f"GET /{self.mountpoint} HTTP/1.0\r\n"
                f"User-Agent: NTRIP PythonClient/1.0\r\n"
                f"Accept: */*\r\n"
                f"Authorization: Basic {auth}\r\n"
                f"Connection: close\r\n"
                f"\r\n"
            )

            # Send request
            self.socket.sendall(request.encode())

            # Check response
            response = self.socket.recv(4096).decode()
            if "ICY 200 OK" not in response:
                raise ConnectionError(f"Server responded with: {response}")

            print("Successfully connected to NTRIP server")
            return True

        except Exception as e:
            print(f"Error connecting to NTRIP server: {e}")
            if self.socket:
                self.socket.close()
            return False

    def read_data(self, buffer_size=1024):
        if not self.socket:
            print("Not connected to server")
            return

        data = None
        try:
            data = self.socket.recv(buffer_size)
        except KeyboardInterrupt:
            print("\nStopping data collection...")
        except Exception as e:
            print(f"Error reading data: {e}")
        finally:
            return data

    def disconnect(self):
        if self.socket:
            self.socket.close()
            self.socket = None
            print("Disconnected from NTRIP server")


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

    def check(self):
        if not self.sta_if.isconnected():
            self.connect()

    def get_mac(self):
        if self.sta_if.isconnected():
            mac_raw = self.sta_if.config("mac")
            mymac = ubin.hexlify(mac_raw).decode()
            return mymac


def main():
    # Load configuration.
    with open("config.json") as cfgf:
        config = json.load(cfgf)

    # WLAN.
    wlan = WLAN(config["wifi"]["ssid"],
                config["wifi"]["password"])
    wlan.connect()

    # UART.
    gps_uart = UARTReceiver(uart_id=2)

    # NMEA decoder.
    mn = MicroNMEA(units=1)

    # NTRIP server.
    ntrip_client = NTRIPClient(config["ntrip"]["host"],
                               config["ntrip"]["port"],
                               config["ntrip"]["mountpoint"],
                               config["ntrip"]["user"],
                               config["ntrip"]["password"])
    ntrip_client.connect()

    # RTK Planner.
    rtkp_url = config["server"]["url"]

    # Data structure to send to RTK Planner.
    gps_data = {
        "fix_status": "Unknowsn",
        "latitude": None,
        "longitude": None,
        "lat_raw": None,
        "lon_raw": None,
        "speed": None,
        "course": None,
        "time_utc": None,
        "last_update": None
    }

    while True:
        mac = wlan.get_mac()
        try:
            response = urequests.post(rtkp_url + "/rover/register",
                                      headers={"Content-Type": "application/json"},
                                      json=json.dumps({"mac": mac}),
                                      timeout=1)
            response_code = response.status_code
            response.close()
            if response_code == 200:
                print("Rover is registered.")
                break
            else:
                print("Rover is NOT registered. Wait for confirmation.")
        except Exception as e:
            print(f"Failed to send mac: {e}")
        time.sleep(2)

    time_start = time.time()
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
                mn.parse(sentence)

                # Send data to RTK Planner server.
                if time_start + 1 < time.time():
                    gps_data["latitude"] = float(mn.lat)
                    gps_data["longitude"] = float(mn.lon)
                    gps_data["fix_status"] = mn.quality
                    gps_data["speed"] = mn.speed
                    gps_data["course"] = mn.course
                    gps_data["time_utc"] = mn.time
                    try:
                        response = urequests.post(rtkp_url + "/rover/update_gps",
                                                  headers={"Content-Type": "application/json"},
                                                  json=json.dumps(gps_data),
                                                  timeout=1)
                        response.close()
                    except Exception as e:
                        print(f"Failed to send data: {e}")
                    time_start = time.time()

        except Exception as e:
            print(f"Main loop error: {e}")


if __name__ == "__main__":
    main()
