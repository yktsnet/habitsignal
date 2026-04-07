# network_manager.py — Unit A
import network
import time
from umqtt.simple import MQTTClient
import config


def connect_wifi():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if wlan.isconnected():
        return wlan
    print(f"WiFi connecting to {config.WIFI_SSID}...")
    wlan.connect(config.WIFI_SSID, config.WIFI_PASSWORD)
    for _ in range(20):
        if wlan.isconnected():
            print(f"WiFi connected: {wlan.ifconfig()[0]}")
            return wlan
        time.sleep(1)
    raise RuntimeError("WiFi connection failed")


def connect_mqtt():
    client = MQTTClient(
        config.MQTT_CLIENT_ID,
        config.MQTT_BROKER,
        port=config.MQTT_PORT,
    )
    client.connect()
    print(f"MQTT connected: {config.MQTT_BROKER}")
    return client
