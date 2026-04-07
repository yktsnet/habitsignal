# buttons.py — Unit A
# タクトスイッチ 3個（上・下・決定）

from machine import Pin
import time

DEBOUNCE_MS = 50


class Buttons:
    def __init__(self, pin_up, pin_down, pin_select):
        self.btn_up = Pin(pin_up, Pin.IN, Pin.PULL_UP)
        self.btn_down = Pin(pin_down, Pin.IN, Pin.PULL_UP)
        self.btn_select = Pin(pin_select, Pin.IN, Pin.PULL_UP)
        self._last_up = 1
        self._last_down = 1
        self._last_select = 1

    def read(self):
        """
        押されたボタンを文字列で返す。
        押されていなければ None。
        チャタリング防止のため立ち下がりエッジを検出する。
        """
        result = None
        up = self.btn_up.value()
        down = self.btn_down.value()
        select = self.btn_select.value()

        if self._last_up == 1 and up == 0:
            time.sleep_ms(DEBOUNCE_MS)
            if self.btn_up.value() == 0:
                result = "up"
        elif self._last_down == 1 and down == 0:
            time.sleep_ms(DEBOUNCE_MS)
            if self.btn_down.value() == 0:
                result = "down"
        elif self._last_select == 1 and select == 0:
            time.sleep_ms(DEBOUNCE_MS)
            if self.btn_select.value() == 0:
                result = "select"

        self._last_up = up
        self._last_down = down
        self._last_select = select
        return result
