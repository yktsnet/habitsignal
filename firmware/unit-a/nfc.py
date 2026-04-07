# nfc.py — Unit A
# PN532 NFC リーダー（I2C）
# タグが読めたらUID文字列を返す。なければ None。

import time


class PN532:
    ADDR = 0x24
    CMD_SAMCONFIGURATION = 0x14
    CMD_INLISTPASSIVETARGET = 0x4A
    PREAMBLE = 0x00
    STARTCODE1 = 0x00
    STARTCODE2 = 0xFF
    POSTAMBLE = 0x00
    HOSTTOPN532 = 0xD4
    PN532TOHOST = 0xD5

    def __init__(self, i2c):
        self.i2c = i2c
        time.sleep_ms(100)
        self._sam_configure()

    def _write_frame(self, data):
        length = len(data)
        lcs = (~length + 1) & 0xFF
        dcs = (~(sum(data)) + 1) & 0xFF
        frame = bytes([
            self.PREAMBLE, self.STARTCODE1, self.STARTCODE2,
            length, lcs, self.HOSTTOPN532
        ]) + bytes(data) + bytes([dcs, self.POSTAMBLE])
        self.i2c.writeto(self.ADDR, frame)

    def _read_response(self, length=64):
        time.sleep_ms(10)
        try:
            data = self.i2c.readfrom(self.ADDR, length)
            # レスポンスフレームのペイロード部分を返す
            # 先頭1バイトはI2Cのステータス、フレーム開始は1バイト目以降
            return data
        except Exception:
            return None

    def _sam_configure(self):
        self._write_frame([self.CMD_SAMCONFIGURATION, 0x01, 0x14, 0x01])
        time.sleep_ms(20)
        self._read_response()

    def read_tag(self):
        """
        NFC タグを1枚読み取ってUID文字列を返す。
        タグがなければ None を返す。
        """
        self._write_frame([self.CMD_INLISTPASSIVETARGET, 0x01, 0x00])
        time.sleep_ms(20)
        response = self._read_response(32)
        if response is None:
            return None
        # レスポンスのパース: PN532 の応答フォーマットに従い UID を抽出
        try:
            # I2C レスポンス: [status, 0x00, 0x00, 0xFF, len, lcs, 0xD5, 0x4B, ...]
            # 実機で確認しながらオフセットを調整すること
            idx = 8  # PN532 応答ヘッダのオフセット（要実機確認）
            if response[idx] == 0x01:  # 1枚検出
                uid_length = response[idx + 5]
                uid = response[idx + 6: idx + 6 + uid_length]
                return "".join(f"{b:02x}" for b in uid)
        except (IndexError, TypeError):
            pass
        return None
