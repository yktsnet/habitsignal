# ld2410.py — Unit B
# LD2410C 24GHz mmWave radar driver
# Returns presence state: "motion" / "still" / "empty" / None

from machine import UART
import time


class LD2410:
    HEADER = bytes([0xF4, 0xF3, 0xF2, 0xF1])
    FOOTER = bytes([0xF8, 0xF7, 0xF6, 0xF5])

    def __init__(self, uart_id, tx, rx, baudrate=256000):
        self.uart = UART(uart_id, baudrate=baudrate, tx=tx, rx=rx, rxbuf=512)
        time.sleep_ms(500)

    def _read_frame(self):
        """Read one data frame from UART buffer. Timeout: 200ms."""
        buf = bytearray()
        deadline = time.ticks_add(time.ticks_ms(), 200)
        while time.ticks_diff(deadline, time.ticks_ms()) > 0:
            if self.uart.any():
                buf += self.uart.read(self.uart.any())
                idx = bytes(buf).find(self.FOOTER)
                if idx >= 4:
                    start = bytes(buf).rfind(self.HEADER, 0, idx)
                    if start >= 0:
                        return bytes(buf[start : idx + 4])
            time.sleep_ms(10)
        return None

    def read_state(self):
        """
        Returns current detection state:
          "motion" — movement detected
          "still"  — stationary presence
          "empty"  — no one detected
          None     — read failed
        """
        frame = self._read_frame()
        if frame is None or len(frame) < 13:
            return None
        if frame[:4] != self.HEADER:
            return None
        target_state = frame[8]
        if target_state == 0x01 or target_state == 0x03:
            return "motion"
        elif target_state == 0x02:
            return "still"
        elif target_state == 0x00:
            return "empty"
        return None
