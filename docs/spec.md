# HabitSignal — Spec

> A personal IoT system that logs desk presence, work sessions, habits, and environment across 4 measurement layers — to observe what conditions help work go well.

---

## Purpose

- Observe whether planned work blocks are actually completed
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
Raw events from sensors and NFC triggers, stored as-is. All aggregation done via SQL — no preprocessing logic in the collector.

| Item | Method | Recorded |
|---|---|---|
| Desk presence | LD2410C mmWave radar | Sampled every 5 min, majority vote over 30 samples |
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
| Temperature / humidity | AHT20 + BMP280 | Timestamp + values every 5 min |
| Now playing | Spotify API (VPS poller, 60s) | Timestamp + track info |
| Audio features | Spotify audio features | energy / valence / tempo |

---

## Database Design (PostgreSQL)

All events share a single `events` table. Analysis is done entirely via SQL queries.

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
- LD2410C samples every 5 min — short absences are not captured
- Work mode depends on manual NFC trigger — missed entries possible
- Subjective score is influenced by immediate emotion at input time
- Correlations do not account for day-of-week, task type, or sample size

---

## Hardware

### Unit B — Presence Sensor (running)

- ESP32-C3
- LD2410C 24GHz mmWave radar (UART, GPIO4/5)

Samples presence state every 10s over a 5-minute window (30 samples). Publishes majority-vote result once per 5 minutes via MQTT. No logic on device beyond sampling.

### Unit A — Main Hub (in progress)

- ESP32-C3
- SSD1306 OLED 1" (I2C 0x3C)
- PN532 NFC reader (I2C 0x24)
- AHT20 + BMP280 (I2C 0x38 / 0x76)

**OLED pages:**
```
[HOME]    Block completion rate / temp+humidity / current mode
[LOG]     Log water / exercise / subjective score
[STATUS]  Today's habit summary
```

### Unit C — Sub Display (planned)

- ESP32-C3
- SSD1306 OLED 1"

---

## System Architecture

```
Unit A (ESP32-C3) ─┐
Unit B (ESP32-C3) ─┼─ MQTT ──→ Mosquitto (VPS)
                   │                 │
                   │          Python collector
                   │          └─ raw events → PostgreSQL
                   │
                   └─ (future) Spotify poller → PostgreSQL
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
| Infra | NixOS / Hetzner VPS |

---

## Design Notes

**Why PostgreSQL over MongoDB or InfluxDB**

InfluxDB is optimized for simple time-series writes but struggles with cross-period comparisons. MongoDB was considered for its schema flexibility, but the VPS resource cost (200–400MB idle RAM) was too high for a shared server already running other services. PostgreSQL with a JSONB payload column covers both needs: structured querying and flexible per-event data.

**Why raw events, not pre-aggregated records**

Storing raw timestamped events keeps the collector simple (no logic) and leaves all interpretation to SQL queries. This makes it easy to ask new questions later without changing the data model.

**Why MQTT over HTTP**

Multiple ESP32-C3 units can publish to the same broker without any per-device endpoint configuration. Adding sensors requires no server-side changes.

**Why majority vote for desk presence**

A single point-in-time sample is too sensitive to momentary sensor noise. Sampling every 10s over 5 minutes (30 samples) and taking a majority vote produces a stable result even when a few samples are lost or misread.
