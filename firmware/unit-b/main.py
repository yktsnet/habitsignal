# main.py — Unit B
# Samples LD2410C every 10s over a 5-minute window (30 samples).
# Majority vote determines desk_on / desk_off.
# Publishes exactly once per 5 minutes to VPS.

import time
import json
import network
from umqtt.simple import MQTTClient
import config
from ld2410 import LD2410

SAMPLE_INTERVAL = 10  # seconds between samples
WINDOW_SAMPLES = 30  # 30 samples = 5 minutes
PING_INTERVAL = 60  # MQTT keepalive


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
    client = MQTTClient(
        config.MQTT_CLIENT_ID, config.MQTT_BROKER, port=config.MQTT_PORT, keepalive=60
    )
    client.connect()
    print(f"MQTT: {config.MQTT_BROKER}")
    return client


def majority_vote(counts):
    """
    Decide desk_on or desk_off from sample counts.
    - any motion → desk_on
    - still > empty → desk_on
    - empty >= still → desk_off
    - all null → desk_off (cannot determine)
    """
    if counts["motion"] > 0:
        return "desk_on", "motion"
    if counts["still"] > counts["empty"]:
        return "desk_on", "still"
    return "desk_off", "empty"


# ── Init ─────────────────────────────────────────────────

connect_wifi()
mqtt = connect_mqtt()
radar = LD2410(uart_id=1, tx=config.UART_TX, rx=config.UART_RX)

print("Unit B ready")

# ── Main loop ─────────────────────────────────────────────

last_ping = time.time()
window_start = time.time()
counts = {"motion": 0, "still": 0, "empty": 0, "null": 0}
sample_count = 0

while True:
    # Sample
    state = radar.read_state()
    if state in counts:
        counts[state] += 1
    else:
        counts["null"] += 1
    sample_count += 1

    # End of window → publish once
    if sample_count >= WINDOW_SAMPLES:
        event_type, reason = majority_vote(counts)
        payload = json.dumps(
            {
                "type": event_type,
                "ts": int(window_start),
                "payload": {
                    "reason": reason,
                    "motion": counts["motion"],
                    "still": counts["still"],
                    "empty": counts["empty"],
                    "null": counts["null"],
                },
            }
        )
        try:
            mqtt.publish(config.TOPIC_EVENTS, payload)
            print(
                f"Published: {event_type} ({reason}) "
                f"motion={counts['motion']} still={counts['still']} "
                f"empty={counts['empty']} null={counts['null']}"
            )
        except Exception as e:
            print(f"MQTT error: {e}")
            try:
                mqtt = connect_mqtt()
                mqtt.publish(config.TOPIC_EVENTS, payload)
            except Exception:
                pass

        # Reset window
        counts = {"motion": 0, "still": 0, "empty": 0, "null": 0}
        sample_count = 0
        window_start = time.time()

    # MQTT keepalive
    now = time.time()
    if now - last_ping > PING_INTERVAL:
        try:
            mqtt.ping()
        except Exception:
            try:
                mqtt = connect_mqtt()
            except Exception:
                pass
        last_ping = now

    time.sleep(SAMPLE_INTERVAL)
