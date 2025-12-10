import socket
from logger import get_logger
try:
    import ubinascii as ubin
except:
    import binascii as ubin


class NTRIPClient:
    def __init__(self, host, port, mountpoint, username, password):
        self.host = host
        self.port = port
        self.mountpoint = mountpoint
        self.username = username
        self.password = password
        self.socket = None
        self.logger = get_logger()

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
                raise ConnectionError(f"NTRIP Server responded with: {response}")

            self.logger.info("NTRIP Successfully connected to server")
            return True

        except Exception as e:
            self.logger.info(f"NTRIP Error connecting to server: {e}")
            if self.socket:
                self.socket.close()
            return False

    def read_data(self, buffer_size=1024):
        if not self.socket:
            self.logger.info("NTRIP Not connected to server")
            return

        data = None
        try:
            data = self.socket.recv(buffer_size)
        except Exception as e:
            self.logger.info(f"NTRIP Error reading data: {e}")
        finally:
            return data

    def disconnect(self):
        if self.socket:
            self.socket.close()
            self.socket = None
            self.logger.info("NTRIP Disconnected from server")
