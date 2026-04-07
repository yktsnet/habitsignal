# デバイス・部品リスト

## Phase 1

### Unit A — メインハブ

| 部品 | 型番 | 用途 | 備考 |
|---|---|---|---|
| マイコン | ESP32C3 | メイン処理・WiFi | 手元にあり |
| ディスプレイ | SSD1306 OLED 1インチ | 状態表示・メニュー操作 | 手元にあり |
| ボタン | タクトスイッチ 3個 | 上・下・決定 | |
| NFC リーダー | PN532 | タグ読み取り | I2C接続 |
| 環境センサー | BME280 | 温度・湿度 | I2C接続 |
| NFC タグ | NTAG213等 | 仕事モード・給水・運動 | 3枚以上 |
| スズメッキ線 | 0.8〜1.0mm | マウント自作 | |
| はんだ | 0.8mm 50g | 接続 | |

**I2C 接続まとめ（SDA/SCL 共有）**
- SSD1306（アドレス: 0x3C）
- BME280（アドレス: 0x76 or 0x77）
- PN532（アドレス: 0x24）

### Unit B — 在席センサー

| 部品 | 型番 | 用途 | 備考 |
|---|---|---|---|
| マイコン | ESP32C3 | MQTT publish | 手元にあり |
| 在席センサー | LD2410C | mmWave 在席検知 | UART接続 |

### VPS 側（Phase 1 で必要なもの）

| ソフトウェア | 用途 |
|---|---|
| Mosquitto | MQTT ブローカー |
| MongoDB | 生データ保存 |
| Python collector | MQTT → MongoDB |

---

## Phase 2

### Unit C — サブ表示

| 部品 | 型番 | 用途 | 備考 |
|---|---|---|---|
| マイコン | ESP32C3 | MQTT subscribe・表示 | 手元にあり |
| ディスプレイ | SSD1306 OLED 1インチ | Spotify・温湿度表示 | 手元にあり |

### VPS 側（Phase 2 追加分）

| ソフトウェア | 用途 |
|---|---|
| Python spotify poller | Spotify API → MongoDB |
| Cloudflare Durable Objects | リアルタイム配信 |
| Astro + Hono | Web ダッシュボード |

---

## Phase 3

追加ハードウェアなし。Demo ページ・README 整備・記事執筆のみ。

---

## ピンアサイン（Unit A）

| ピン | 用途 |
|---|---|
| GPIO6 | I2C SDA（OLED・BME280・PN532 共有） |
| GPIO7 | I2C SCL（OLED・BME280・PN532 共有） |
| GPIO0 | ボタン 上 |
| GPIO1 | ボタン 下 |
| GPIO2 | ボタン 決定 |

## ピンアサイン（Unit B）

| ピン | 用途 |
|---|---|
| GPIO20 | UART RX（LD2410C TX） |
| GPIO21 | UART TX（LD2410C RX） |
