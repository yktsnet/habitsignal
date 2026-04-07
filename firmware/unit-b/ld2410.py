# ld2410.py — Unit B
# LD2410C mmWave レーダー（UART）
# 在席・離席の変化のみを返す。生データは持たない。

from machine import UART
import time


class LD2410:
    """
    LD2410C の UART 出力を読み取り、在席状態を返す。

    LD2410C のデフォルト出力:
      フレーム先頭: F4 F3 F2 F1
      フレーム末尾: F8 F7 F6 F5
      データ部 [8] の値:
        0x00 = 無人
        0x01 = 動きあり
        0x02 = 静止あり（微細動き含む）
    """
    HEADER = bytes([0xF4, 0xF3, 0xF2, 0xF1])
    FOOTER = bytes([0xF8, 0xF7, 0xF6, 0xF5])

    def __init__(self, uart_id, tx, rx, baudrate=256000):
        self.uart = UART(uart_id, baudrate=baudrate, tx=tx, rx=rx)
        time.sleep_ms(100)

    def _read_frame(self):
        """1フレーム読み取る。タイムアウトしたら None を返す。"""
        buf = bytearray()
        deadline = time.ticks_add(time.ticks_ms(), 200)
        while time.ticks_diff(deadline, time.ticks_ms()) > 0:
            if self.uart.any():
                buf += self.uart.read(1)
                if len(buf) >= 4 and buf[-4:] == self.FOOTER:
                    return bytes(buf)
        return None

    def read_presence(self):
        """
        在席状態を返す。
          True  = 在席（動き or 静止検知）
          False = 離席
          None  = 読み取り失敗
        """
        frame = self._read_frame()
        if frame is None or len(frame) < 13:
            return None
        # フレーム検証
        if frame[:4] != self.HEADER:
            return None
        target_state = frame[8]  # 0x00=無人, 0x01=動き, 0x02=静止
        return target_state != 0x00
