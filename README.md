# HabitSignal

> A personal IoT system that logs desk presence, work sessions, habits, and environment across 4 measurement layers — to observe what conditions help work go well.

## Status

- **Unit B** (presence sensor) — running, recording every 5 min
- **Unit A** (main hub: NFC, OLED, env sensor) — in progress
- **VPS** (Mosquitto + PostgreSQL + collector) — running

## Measurement Layers

| Layer | What | How |
|---|---|---|
| Layer 1 | Plan (target blocks) | Pre-configured |
| Layer 2 | Actual (objective) | Sensors + NFC triggers |
| Layer 3 | Subjective score | Manual input via OLED menu |
| Layer 4 | Conditions | AHT20/BMP280 + Spotify API |

## Hardware

| Unit | Role | Components |
|---|---|---|
| Unit A | Main hub (desk) | ESP32-C3, SSD1306 OLED, PN532 NFC, AHT20+BMP280 |
| Unit B | Presence sensor | ESP32-C3, LD2410C 24GHz mmWave radar |
| Unit C | Sub display *(planned)* | ESP32-C3, SSD1306 OLED |

## Architecture

```
Unit A (ESP32-C3) ─┐
Unit B (ESP32-C3) ─┼─ MQTT ──→ Mosquitto (VPS) ──→ PostgreSQL
```

## Stack

| Layer | Tech |
|---|---|
| Firmware | MicroPython |
| Transport | MQTT over WiFi |
| Broker | Mosquitto |
| Collector | Python (systemd service, NixOS) |
| DB | PostgreSQL (JSONB for event payloads) |
| Infra | NixOS / Hetzner VPS |

## Repository Structure

```
firmware/
  unit-a/     Main hub firmware
  unit-b/     Presence sensor firmware
  unit-c/     Sub display firmware (planned)
server/
  collector/  MQTT → PostgreSQL
  spotify/    Spotify poller (planned)
infra/        NixOS service definitions
docs/         Spec, wiring diagrams
```

## Docs

- [Spec](docs/spec.md)
- [Unit A Wiring](docs/wiring-unit-a.d2)
- [Unit B Wiring](docs/wiring-unit-b.d2)
