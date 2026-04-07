# sensors.py — Unit A
# AHT20 + BMP280 複合モジュール（I2C）

import time


class AHT20:
    """AHT20 温湿度センサー"""
    ADDR = 0x38
    CMD_INIT = bytes([0xBE, 0x08, 0x00])
    CMD_MEASURE = bytes([0xAC, 0x33, 0x00])

    def __init__(self, i2c):
        self.i2c = i2c
        self._init()

    def _init(self):
        time.sleep_ms(40)
        self.i2c.writeto(self.ADDR, self.CMD_INIT)
        time.sleep_ms(10)

    def read(self):
        self.i2c.writeto(self.ADDR, self.CMD_MEASURE)
        time.sleep_ms(80)
        data = self.i2c.readfrom(self.ADDR, 6)
        humidity = ((data[1] << 12) | (data[2] << 4) | (data[3] >> 4)) / 1048576 * 100
        temp = (((data[3] & 0x0F) << 16) | (data[4] << 8) | data[5]) / 1048576 * 200 - 50
        return round(temp, 1), round(humidity, 1)


class BMP280:
    """BMP280 気圧・温度センサー（気圧のみ使用）"""
    ADDR = 0x76  # SDO → GND の場合。HIGH なら 0x77

    def __init__(self, i2c):
        self.i2c = i2c
        self._load_calibration()

    def _read_reg(self, reg, length):
        return self.i2c.readfrom_mem(self.ADDR, reg, length)

    def _load_calibration(self):
        import struct
        raw = self._read_reg(0x88, 24)
        self.dig = struct.unpack("<HhhHhhhhhhhh", raw[:24])

    def read_pressure(self):
        raw = self._read_reg(0xF7, 6)
        adc_P = (raw[0] << 12) | (raw[1] << 4) | (raw[2] >> 4)
        adc_T = (raw[3] << 12) | (raw[4] << 4) | (raw[5] >> 4)
        # 温度補正（内部計算用）
        var1 = (adc_T / 16384 - self.dig[0] / 1024) * self.dig[1]
        var2 = (adc_T / 131072 - self.dig[0] / 8192) ** 2 * self.dig[2]
        t_fine = var1 + var2
        # 気圧計算
        var1 = t_fine / 2 - 64000
        var2 = var1 * var1 * self.dig[8] / 32768
        var2 = var2 + var1 * self.dig[7] * 2
        var2 = var2 / 4 + self.dig[6] * 65536
        var1 = (self.dig[5] * var1 * var1 / 524288 + self.dig[4] * var1) / 524288 + 1
        pressure = 1048576 - adc_P
        pressure = (pressure - var2 / 4096) * 6250 / var1
        return round(pressure / 100, 1)  # hPa


class EnvSensor:
    """AHT20 + BMP280 をまとめて扱うラッパー"""
    def __init__(self, i2c):
        self.aht20 = AHT20(i2c)
        self.bmp280 = BMP280(i2c)

    def read(self):
        temp, humidity = self.aht20.read()
        return {
            "temp": temp,
            "humidity": humidity,
        }
