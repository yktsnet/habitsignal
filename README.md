# HabitSignal

> A personal IoT system that logs behavior, environment, and subjective scores across 4 measurement layers — to observe what conditions help work go well.

## Architecture

```
Unit A (ESP32-C3) ─┐
Unit B (ESP32-C3) ─┼─ MQTT ──→ Mosquitto (VPS) ──→ PostgreSQL
                   │                                     │
                   │                         Cloudflare Durable Objects
                   └──────────────────────────── SSE ──→ Web Dashboard
```

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
| Unit B | Presence sensor (under desk) | ESP32-C3, LD2410C mmWave radar |
| Unit C | Sub display *(Phase 2)* | ESP32-C3, SSD1306 OLED |

## Stack

| Layer | Tech |
|---|---|
| Firmware | MicroPython |
| Transport | MQTT over WiFi |
| Broker | Mosquitto |
| Collector | Python (systemd service) |
| DB | PostgreSQL (JSONB for payloads) |
| External API | Spotify Web API |
| Realtime | Cloudflare Durable Objects + SSE |
| Frontend | Astro + Hono |
| Infra | NixOS / Hetzner VPS |

## Repository Structure

```
firmware/
  unit-a/     Main hub firmware
  unit-b/     Presence sensor firmware
  unit-c/     Sub display firmware (Phase 2)
server/
  collector/  MQTT → PostgreSQL
  spotify/    Spotify poller (Phase 2)
infra/        NixOS service definitions
docs/         Wiring diagrams, spec
```

## Docs

- [Spec](docs/spec.md)
- [Unit A Wiring](docs/wiring-unit-a.d2)
- [Unit B Wiring](docs/wiring-unit-b.d2)
