# display.py — Unit A
# SSD1306 OLED 1インチ メニュー表示

import time
from ssd1306 import SSD1306_I2C

WIDTH = 128
HEIGHT = 64

# ページ定義
PAGE_HOME = 0
PAGE_LOG = 1
PAGE_STATUS = 2
PAGES = [PAGE_HOME, PAGE_LOG, PAGE_STATUS]
PAGE_NAMES = ["HOME", "LOG", "STATUS"]

# LOG ページのメニュー項目
LOG_ITEMS = ["Water", "Exercise", "Score: 1", "Score: 2", "Score: 3", "Score: 4", "Score: 5"]


class Display:
    def __init__(self, i2c):
        self.oled = SSD1306_I2C(WIDTH, HEIGHT, i2c)
        self.page = PAGE_HOME
        self.log_cursor = 0

    # ── ページ切り替え ──────────────────────────────────

    def next_page(self):
        self.page = (self.page + 1) % len(PAGES)
        self.log_cursor = 0

    # ── LOG ページのカーソル操作 ────────────────────────

    def cursor_up(self):
        if self.page == PAGE_LOG:
            self.log_cursor = (self.log_cursor - 1) % len(LOG_ITEMS)

    def cursor_down(self):
        if self.page == PAGE_LOG:
            self.log_cursor = (self.log_cursor + 1) % len(LOG_ITEMS)

    def get_log_selection(self):
        """現在のカーソル位置のアイテムを返す"""
        return LOG_ITEMS[self.log_cursor]

    # ── 描画 ────────────────────────────────────────────

    def render(self, state):
        self.oled.fill(0)
        if self.page == PAGE_HOME:
            self._render_home(state)
        elif self.page == PAGE_LOG:
            self._render_log()
        elif self.page == PAGE_STATUS:
            self._render_status(state)
        self.oled.show()

    def _render_home(self, state):
        # 1行目: ページ名
        self.oled.text("[ HOME ]", 0, 0)
        # 2行目: 仕事モード
        mode = "WORK ON " if state.get("work_mode") else "WORK OFF"
        self.oled.text(mode, 0, 16)
        # 3行目: 温湿度
        temp = state.get("temp", "--")
        hum = state.get("humidity", "--")
        self.oled.text(f"{temp}C  {hum}%", 0, 32)
        # 4行目: 今日の仕事時間
        minutes = state.get("work_minutes_today", 0)
        h, m = divmod(minutes, 60)
        self.oled.text(f"Work: {h:02d}h{m:02d}m", 0, 48)

    def _render_log(self):
        self.oled.text("[ LOG ]", 0, 0)
        # 最大4項目表示（スクロール対応）
        start = max(0, self.log_cursor - 1)
        for i, item in enumerate(LOG_ITEMS[start:start + 4]):
            y = 16 + i * 12
            cursor = ">" if (start + i) == self.log_cursor else " "
            self.oled.text(f"{cursor}{item}", 0, y)

    def _render_status(self, state):
        self.oled.text("[ STATUS ]", 0, 0)
        water = state.get("water_count", 0)
        self.oled.text(f"Water: {water}x", 0, 16)
        exercise = "Done" if state.get("exercise_today") else "None"
        self.oled.text(f"Exercise: {exercise}", 0, 32)
        score = state.get("last_score", "-")
        self.oled.text(f"Last score: {score}", 0, 48)

    def show_message(self, msg, duration_ms=1000):
        """一時的なメッセージ表示"""
        self.oled.fill(0)
        self.oled.text(msg, 0, 24)
        self.oled.show()
        time.sleep_ms(duration_ms)
