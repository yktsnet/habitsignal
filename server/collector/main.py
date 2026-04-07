# main.py — collector
# MQTT subscriber → stores raw events into PostgreSQL
# No logic on the Python side — all analysis done via SQL queries

import json
import os

import paho.mqtt.client as mqtt
import psycopg2
import psycopg2.extras

MQTT_BROKER = os.getenv("MQTT_BROKER", "localhost")
MQTT_PORT = int(os.getenv("MQTT_PORT", 1883))
MQTT_TOPIC = os.getenv("MQTT_TOPIC", "habitsignal/events")
PG_DSN = os.getenv("PG_DSN", "postgresql://habitsignal@localhost/habitsignal")

# PostgreSQL 接続
conn = psycopg2.connect(PG_DSN)
conn.autocommit = True

# テーブル初期化（初回のみ実行）
with conn.cursor() as cur:
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS events (
            id        SERIAL PRIMARY KEY,
            type      TEXT NOT NULL,
            ts        BIGINT NOT NULL,
            server_ts TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            payload   JSONB
        );
        CREATE INDEX IF NOT EXISTS events_ts_idx   ON events (ts);
        CREATE INDEX IF NOT EXISTS events_type_idx ON events (type);
    """
    )

print(f"PostgreSQL connected: {PG_DSN}")


def on_connect(client, userdata, flags, rc):
    print(f"MQTT connected (rc={rc})")
    client.subscribe(MQTT_TOPIC)


def on_message(client, userdata, msg):
    try:
        data = json.loads(msg.payload.decode())
    except json.JSONDecodeError as e:
        print(f"JSON error: {e} | raw: {msg.payload}")
        return

    if "type" not in data:
        print(f"No type field, skipped: {data}")
        return

    event_type = data["type"]
    ts = data.get("ts", 0)
    payload = data.get("payload")

    with conn.cursor() as cur:
        cur.execute(
            "INSERT INTO events (type, ts, payload) VALUES (%s, %s, %s)",
            (event_type, ts, json.dumps(payload) if payload else None),
        )

    print(f"Saved: {event_type} (ts={ts})")


client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

print(f"Connecting to MQTT: {MQTT_BROKER}:{MQTT_PORT}")
client.connect(MQTT_BROKER, MQTT_PORT, keepalive=60)
client.loop_forever()
