# HabitSignal — Spec

> A personal IoT system that logs behavior, environment, and subjective scores across 4 measurement layers — to observe what conditions help work go well.

---

## Purpose

- Track whether planned work blocks (morning / afternoon / evening) are completed
- Correlate the subjective feeling of "things went well" with environmental and behavioral data
- Build hypotheses about what conditions improve focus — from your own data

**Note:** This system measures proxy indicators, not productivity itself. Correlation observed does not imply causation.

---

## Measurement Layers

### Layer 1 — Plan
Pre-configured targets. Not measured — used as the baseline.

- Work block definitions with planned durations
- Example: Morning 3h / Afternoon 2h / Evening 1.5h
- Structure can vary day to day

### Layer 2 — Actual (Objective)
Raw events from sensors and NFC triggers, stored as-is. No logic on the Python side — all aggregation via SQL queries.

| Item | Method | Recorded |
|---|---|---|
| Desk presence | LD2410C mmWave radar | Timestamps of on/off transitions |
| Work mode | NFC tag / button | ON/OFF timestamps |
| Hydration | NFC tag / button | Timestamps |
| Exercise | NFC tag / button | Start / end / type timestamps |

### Layer 3 — Subjective Score
Entered manually via OLED menu at the end of each work block.

- 1–5 rating for how well the block went
- Stored with timestamp, linked to the block by time range

### Layer 4 — Conditions
Variables that may influence Layer 2 and 3. Stored as raw events.

| Item | Method | Recorded |
|---|---|---|
| Temperature / humidity | AHT20 + BMP280 | Timestamp + values |
| Now playing | Spotify API (VPS poller, 60s) | Timestamp + track info |
| Audio features | Spotify audio features | energy / valence / tempo |

---

## Database Design (PostgreSQL)

All events are stored in a single `events` table. Analysis is done via SQL queries — no preprocessing logic in Python.

```sql
CREATE TABLE events (
    id        SERIAL PRIMARY KEY,
    type      TEXT NOT NULL,
    ts        BIGINT NOT NULL,
    server_ts TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    payload   JSONB
);
```

**Event types:** `desk_on`, `desk_off`, `work_on`, `work_off`, `water`, `exercise_start`, `exercise_end`, `env`, `spotify`, `score`

**Example queries:**
- Work minutes per day → filter `work_on/off`, group by date
- Score vs environment → join `score` events with `env` events within ±30 min
- Exercise days → distinct dates with `exercise_start`

---

## Correlations to Explore

- Layer 4 → Layer 2: Do conditions affect block completion rate?
- Layer 4 → Layer 3: Do conditions affect subjective score?
- Layer 2 vs Layer 3 gap: High completion but low score — or vice versa

### Initial Hypotheses
1. Higher room temperature → shorter work mode durations?
2. Exercise days → higher afternoon block completion?
3. High-energy music (tempo > 130) → higher subjective score?
4. Fewer hydration events → lower subjective score?

### Known Measurement Limitations
- LD2410C may misfire from wall/object reflections
- Work mode depends on manual NFC trigger — missed entries possible
- Subjective score is influenced by immediate emotion at input time
- Correlations do not account for day-of-week, task type, or sample size

---

## Hardware

### Unit A — Main Hub (desk)

- ESP32-C3
- SSD1306 OLED 1"
- PN532 NFC reader (I2C mode)
- AHT20 + BMP280 (I2C)

**OLED pages:**
```
[HOME]    Block completion rate / temp+humidity / current mode
[LOG]     Log water / exercise / subjective score
[STATUS]  Today's habit summary
```

**NFC tag assignments:**
- Work mode toggle (desk side)
- Hydration log (near water)
- Exercise start/end (near equipment)

### Unit B — Presence Sensor (under desk)

- ESP32-C3
- LD2410C 24GHz mmWave radar

Detects presence changes and publishes `desk_on` / `desk_off` via MQTT. No logic on device.

### Unit C — Sub Display *(Phase 2)*

- ESP32-C3
- SSD1306 OLED 1"

Subscribes to MQTT and displays Spotify now-playing and current temperature. Display only — no logic.

---

## System Architecture

```
Unit A (ESP32-C3) ─┐
Unit B (ESP32-C3) ─┼─ MQTT ──→ Mosquitto (VPS)
                   │                 │
                   │          Python collector
                   │          ├─ raw events → PostgreSQL
                   │          └─ Spotify poller (60s) → PostgreSQL
                   │                 │
                   │           PostgreSQL
                   │          (SQL queries for analysis)
                   │                 │
                   │    Cloudflare Durable Objects
                   │                 │
                   └──── SSE ──→ Web Dashboard (Astro + Hono)
```

---

## Stack

| Layer | Tech |
|---|---|
| Firmware | MicroPython |
| Transport | MQTT over WiFi |
| Broker | Mosquitto |
| Collector | Python (systemd service, NixOS) |
| DB | PostgreSQL (JSONB for payloads) |
| External API | Spotify Web API |
| Realtime | Cloudflare Durable Objects + SSE |
| Frontend | Astro + Hono |
| Infra | NixOS / Hetzner VPS |

---

## Design Notes

**Why PostgreSQL over MongoDB or InfluxDB**

InfluxDB is optimized for simple time-series writes but struggles with cross-block comparisons. MongoDB was considered for its schema flexibility, but the VPS resource cost (200–400MB idle RAM) was too high for a shared server already running other services. PostgreSQL with a JSONB payload column covers both needs: structured querying and flexible per-event data.

**Why raw events, not pre-aggregated documents**

Storing raw timestamped events keeps the collector simple (no logic) and leaves all interpretation to SQL queries. This makes it easy to ask new questions later without changing the data model.

**Why MQTT over HTTP**

Multiple ESP32-C3 units can publish to the same broker without any per-device endpoint configuration. Adding Unit C or future sensors requires no server-side changes.
