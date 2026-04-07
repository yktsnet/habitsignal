# main.py — collector
# MQTT subscriber → MongoDB へ生データをそのまま保存する
# Python 側にロジックは持たない

import json
import os
from datetime import datetime, timezone

import paho.mqtt.client as mqtt
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

MQTT_BROKER = os.getenv("MQTT_BROKER", "localhost")
MQTT_PORT = int(os.getenv("MQTT_PORT", 1883))
MQTT_TOPIC = os.getenv("MQTT_TOPIC", "habitsignal/events")

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
MONGO_DB = os.getenv("MONGO_DB", "habitsignal")

# MongoDB 接続
mongo = MongoClient(MONGO_URI)
db = mongo[MONGO_DB]
events = db["events"]

# インデックス（初回のみ作成される）
events.create_index([("ts", 1)])
events.create_index([("type", 1)])


def on_connect(client, userdata, flags, rc):
    print(f"MQTT connected (rc={rc})")
    client.subscribe(MQTT_TOPIC)


def on_message(client, userdata, msg):
    try:
        data = json.loads(msg.payload.decode())
    except json.JSONDecodeError as e:
        print(f"JSON error: {e} | raw: {msg.payload}")
        return

    # ESP32 の time.time() は Unix タイムスタンプだが NTP 未同期の場合がある
    # サーバー側でも受信時刻を付与しておく
    data["server_ts"] = datetime.now(timezone.utc)

    # type フィールドがなければ捨てる
    if "type" not in data:
        print(f"No type field, skipped: {data}")
        return

    result = events.insert_one(data)
    print(f"Saved: {data['type']} → {result.inserted_id}")


client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

print(f"Connecting to MQTT broker: {MQTT_BROKER}:{MQTT_PORT}")
client.connect(MQTT_BROKER, MQTT_PORT, keepalive=60)
client.loop_forever()
