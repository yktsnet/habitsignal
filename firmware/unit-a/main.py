# main.py — Unit A
# メインハブ: NFC・ボタン・OLED・BME280 + AHT20

import time
import json
from machine import I2C, Pin
import config
from network_manager import connect_wifi, connect_mqtt
from sensors import EnvSensor
from nfc import PN532
from display import Display
from buttons import Buttons

# ── 初期化 ──────────────────────────────────────────────

i2c = I2C(0, sda=Pin(config.I2C_SDA), scl=Pin(config.I2C_SCL), freq=400000)

display = Display(i2c)
sensor = EnvSensor(i2c)
nfc = PN532(i2c)
buttons = Buttons(config.BTN_UP, config.BTN_DOWN, config.BTN_SELECT)

display.show_message("Connecting...", 500)
connect_wifi()
mqtt = connect_mqtt()
display.show_message("Ready", 500)

# ── 状態管理 ─────────────────────────────────────────────

state = {
    "work_mode": False,
    "work_mode_start": None,
    "work_minutes_today": 0,
    "temp": None,
    "humidity": None,
    "water_count": 0,
    "exercise_today": False,
    "exercise_start": None,
    "last_score": None,
}

# ── イベント publish ──────────────────────────────────────

def publish_event(event_type, payload=None):
    data = {"type": event_type, "ts": time.time()}
    if payload:
        data["payload"] = payload
    mqtt.publish(config.TOPIC_EVENTS, json.dumps(data))
    print(f"Published: {event_type}")

# ── NFC タグ処理 ─────────────────────────────────────────

def handle_nfc(uid):
    event_type = config.NFC_TAG_MAP.get(uid)
    if event_type is None:
        print(f"Unknown tag: {uid}")
        display.show_message(f"Tag: {uid[:8]}", 1000)
        return
    handle_event(event_type)

# ── イベント処理 ─────────────────────────────────────────

def handle_event(event_type, extra=None):
    if event_type == "work_toggle":
        if not state["work_mode"]:
            state["work_mode"] = True
            state["work_mode_start"] = time.time()
            publish_event("work_on")
            display.show_message("WORK ON", 800)
        else:
            state["work_mode"] = False
            if state["work_mode_start"]:
                elapsed = (time.time() - state["work_mode_start"]) // 60
                state["work_minutes_today"] += elapsed
            publish_event("work_off")
            display.show_message("WORK OFF", 800)

    elif event_type == "water":
        state["water_count"] += 1
        publish_event("water")
        display.show_message(f"Water x{state['water_count']}", 800)

    elif event_type == "exercise_start":
        state["exercise_start"] = time.time()
        publish_event("exercise_start")
        display.show_message("Exercise start", 800)

    elif event_type == "exercise_end":
        state["exercise_today"] = True
        publish_event("exercise_end")
        display.show_message("Exercise done", 800)

    elif event_type and event_type.startswith("score_"):
        score = int(event_type.split("_")[1])
        state["last_score"] = score
        publish_event("score", {"value": score})
        display.show_message(f"Score: {score}", 800)

# ── LOG ページの選択処理 ─────────────────────────────────

def handle_log_selection(item):
    if item == "Water":
        handle_event("water")
    elif item == "Exercise":
        if not state["exercise_today"]:
            handle_event("exercise_start")
        else:
            handle_event("exercise_end")
    elif item.startswith("Score: "):
        score = item.split(": ")[1]
        handle_event(f"score_{score}")

# ── 環境センサー定期取得 ─────────────────────────────────

ENV_INTERVAL = 300  # 5分
last_env_ts = 0

def update_env():
    global last_env_ts
    now = time.time()
    if now - last_env_ts < ENV_INTERVAL:
        return
    try:
        result = sensor.read()
        state["temp"] = result["temp"]
        state["humidity"] = result["humidity"]
        publish_event("env", result)
        last_env_ts = now
    except Exception as e:
        print(f"Sensor error: {e}")

# ── メインループ ─────────────────────────────────────────

DISPLAY_REFRESH = 2000  # ms
last_display_ts = 0

while True:
    # ボタン処理
    btn = buttons.read()
    if btn == "up":
        if display.page == 1:
            display.cursor_up()
        else:
            display.next_page()
    elif btn == "down":
        if display.page == 1:
            display.cursor_down()
        else:
            display.next_page()
    elif btn == "select":
        if display.page == 1:
            handle_log_selection(display.get_log_selection())
        else:
            display.next_page()

    # NFC タグ読み取り
    uid = nfc.read_tag()
    if uid:
        handle_nfc(uid)
        time.sleep_ms(500)  # 連続読み取り防止

    # 環境センサー更新
    update_env()

    # OLED 更新
    now_ms = time.ticks_ms()
    if time.ticks_diff(now_ms, last_display_ts) > DISPLAY_REFRESH:
        display.render(state)
        last_display_ts = now_ms

    # MQTT keepalive
    try:
        mqtt.ping()
    except Exception:
        mqtt = connect_mqtt()

    time.sleep_ms(50)
