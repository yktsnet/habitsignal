# config.py — Unit A
# 実環境に合わせて編集する

WIFI_SSID = "your_ssid"
WIFI_PASSWORD = "your_password"

MQTT_BROKER = "91.98.173.78"
MQTT_PORT = 1883
MQTT_CLIENT_ID = "habitsignal-unit-a"

# I2C ピン
I2C_SDA = 6
I2C_SCL = 7

# ボタン GPIO
BTN_UP = 0
BTN_DOWN = 1
BTN_SELECT = 2

# NFC タグ ID → イベント種別のマッピング
# タグを読み取ったら `habitsignal/events` に publish する
NFC_TAG_MAP = {
    # "タグIDの16進数文字列": "イベント種別",
    # 例: "04a1b2c3": "work_toggle",
    # 実際のタグIDは起動後のシリアルログで確認する
}

# MQTT トピック
TOPIC_EVENTS = b"habitsignal/events"
TOPIC_STATUS = b"habitsignal/status"
