# main.py — Unit B
# 在席センサー: LD2410C → MQTT publish のみ

import time
import json
import network
from machine import Pin
from umqtt.simple import MQTTClient
import config
from ld2410 import LD2410


def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if wlan.isconnected():
        return wlan
    wlan.connect(config.WIFI_SSID, config.WIFI_PASSWORD)
    for _ in range(20):
        if wlan.isconnected():
            print(f"WiFi: {wlan.ifconfig()[0]}")
            return wlan
        time.sleep(1)
    raise RuntimeError("WiFi failed")


def connect_mqtt():
    client = MQTTClient(config.MQTT_CLIENT_ID, config.MQTT_BROKER, port=config.MQTT_PORT)
    client.connect()
    return client


# ── 初期化 ────────────────────────────────────────────────

connect_wifi()
mqtt = connect_mqtt()
radar = LD2410(uart_id=1, tx=config.UART_TX, rx=config.UART_RX)

# ── 状態管理 ─────────────────────────────────────────────
# 変化があったときだけ publish する（毎秒 publish しない）

last_presence = None
PING_INTERVAL = 30  # 秒ごとに MQTT keepalive
last_ping = time.time()

print("Unit B ready")

while True:
    presence = radar.read_presence()

    if presence is not None and presence != last_presence:
        event_type = "desk_on" if presence else "desk_off"
        payload = json.dumps({"type": event_type, "ts": time.time()})
        try:
            mqtt.publish(config.TOPIC_EVENTS, payload)
            print(f"Published: {event_type}")
        except Exception as e:
            print(f"MQTT error: {e}")
            try:
                mqtt = connect_mqtt()
            except Exception:
                pass
        last_presence = presence

    # MQTT keepalive
    now = time.time()
    if now - last_ping > PING_INTERVAL:
        try:
            mqtt.ping()
        except Exception:
            mqtt = connect_mqtt()
        last_ping = now

    time.sleep_ms(500)
