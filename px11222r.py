from machine import UART

try:
    import ubinascii as ubin
except:
    import binascii as ubin


class PX1122RUART:
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
