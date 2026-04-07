# HabitSignal

> 自宅作業における行動・環境・主観を4レイヤーで計測し、
> 仕事が進みやすい条件の傾向を自分で観測するためのシステム

## Architecture

```
Unit A（ESP32C3）─┐
Unit B（ESP32C3）─┼─ MQTT ──→ Mosquitto（VPS）──→ MongoDB
Unit C（ESP32C3）─┘                                    │
   ↑ MQTT subscribe                        Cloudflare Durable Objects
   └───────────────────────────────────────────── SSE ──→ Web
```

## Layers

| Layer | 内容 | 手段 |
|---|---|---|
| Layer 1 | 目標（計画） | 事前設定 |
| Layer 2 | 実績（客観計測） | センサー・NFC・ボタン |
| Layer 3 | 主観（自己評価） | OLED メニューから入力 |
| Layer 4 | 条件（環境・音楽） | BME280・Spotify API |

## Structure

```
firmware/
  unit-a/   メインハブ（NFC・ボタン・OLED・BME280）
  unit-b/   在席センサー（LD2410C）
  unit-c/   サブ表示（OLED・Spotify・温湿度）
server/
  collector/  MQTT → MongoDB
  spotify/    Spotify poller
infra/        NixOS / systemd 設定
docs/         設計ドキュメント
```

## Docs

- [仕様書](docs/spec.md)
- [デバイス・部品リスト](docs/devices.md)
