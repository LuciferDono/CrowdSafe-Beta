# CrowdSafe Metrics & Configuration Guide

## Table of Contents

1. [Input Parameters](#1-input-parameters)
2. [Risk Formula](#2-risk-formula)
3. [Risk Levels & Thresholds](#3-risk-levels--thresholds)
4. [Alert Trigger Conditions](#4-alert-trigger-conditions)
5. [Parameter Impact Analysis](#5-parameter-impact-analysis)
6. [Scenario Presets](#6-scenario-presets)
7. [Real-World Density Reference](#7-real-world-density-reference)

---

## 1. Input Parameters

When adding a camera/video, two key parameters are configured:

| Parameter | Description | Default | Unit |
|---|---|---|---|
| `area_sqm` | Physical area the camera covers | 100.0 | m² |
| `expected_capacity` | Max expected people in the area | 500 | count |

### How They're Used

```
density          = people_count / area_sqm          (p/m²)
capacity_util    = (people_count / expected_capacity) × 100   (%)
```

- **`area_sqm`** directly controls density, which drives risk scoring and alerts. This is the most critical parameter.
- **`expected_capacity`** only affects the capacity utilization display metric. It does NOT influence risk score or alerts.

---

## 2. Risk Formula

```
Risk_Score = Base Score + ML Boosts
```

### Base Score (Weighted Sum)

```
Base = (W_density × density_norm) + (W_surge × surge_norm) + (W_velocity × velocity_inv_norm)
```

| Component | Weight | Normalization | Range |
|---|---|---|---|
| Density | 0.4 (40%) | `min(1.0, density / 10.0)` | 0.0 - 1.0 |
| Surge Rate | 0.3 (30%) | `min(1.0, surge_rate / 2.0)` | 0.0 - 1.0 |
| Velocity (inverse) | 0.3 (30%) | See below | 0.0 - 1.0 |

### Velocity Normalization (Lower velocity = Higher risk)

| Avg Velocity | Normalized Value | Meaning |
|---|---|---|
| <= 0.2 m/s | 1.0 (max risk) | Stagnant / stuck |
| 0.5 m/s | 0.77 | Slow shuffle |
| 0.8 m/s | 0.54 | Reduced movement |
| 1.0 m/s | 0.38 | Moderate walking |
| 1.5+ m/s | 0.0 (no risk) | Free movement |

Formula: `velocity_inv_norm = 1.0 - ((velocity - 0.2) / 1.3)` (clamped 0-1)

### ML Boosts

| Signal | Formula | Max Boost | Trigger |
|---|---|---|---|
| Crowd Pressure | `max(0, pressure - 0.3) × 0.15` | +0.105 | Pressure > 0.3 |
| Flow Coherence | `max(0, coherence - 0.5) × 0.2` | +0.10 | Coherence > 0.5 |
| Large Crowd | `risk × 1.15` | ×1.15 | Count > 100 |

### Full Formula

```
risk = 0.4 × min(1, density/10)
     + 0.3 × min(1, surge/2)
     + 0.3 × velocity_inv_norm
     + max(0, pressure - 0.3) × 0.15
     + max(0, coherence - 0.5) × 0.2

if count > 100: risk *= 1.15
risk = clamp(risk, 0.0, 1.0)
```

---

## 3. Risk Levels & Thresholds

| Level | Score Range | Color | Action |
|---|---|---|---|
| **SAFE** | 0% - 24% | Green | Normal monitoring |
| **CAUTION** | 25% - 49% | Yellow | Increased attention |
| **WARNING** | 50% - 74% | Orange | Alert triggered, Telegram sent |
| **CRITICAL** | 75% - 100% | Red | Immediate action, Telegram sent |

---

## 4. Alert Trigger Conditions

Alerts are created when risk reaches WARNING or CRITICAL, subject to a cooldown period (default: 60 seconds per camera per level).

### Trigger Types

| Trigger | Condition | Priority |
|---|---|---|
| `extreme_density` | `density > 6.0 p/m²` | Highest |
| `sudden_surge` | `surge_rate > 0.8` | High |
| `stagnation_with_density` | `velocity < 0.2 m/s AND density > 4.0` | High |
| `risk_threshold` | Risk level >= WARNING (fallback) | Normal |

### Notification Channels

| Channel | Trigger Level | Status |
|---|---|---|
| Dashboard (SocketIO) | WARNING, CRITICAL | Active |
| Telegram Bot | WARNING, CRITICAL | Active |
| Email (SMTP) | - | Not implemented |
| SMS (Twilio) | - | Not implemented |

---

## 5. Parameter Impact Analysis

### Effect of `area_sqm` on Density & Risk

**Smaller area = Higher density = Earlier alerts**

#### With 20 people detected:

| area_sqm | Density | Density Norm | Risk (density only) | Approx Level |
|---|---|---|---|---|
| 2 | 10.0 p/m² | 1.00 | 0.40 | CAUTION-WARNING |
| 3 | 6.67 p/m² | 0.67 | 0.27 | CAUTION |
| 5 | 4.00 p/m² | 0.40 | 0.16 | SAFE-CAUTION |
| 10 | 2.00 p/m² | 0.20 | 0.08 | SAFE |
| 50 | 0.40 p/m² | 0.04 | 0.02 | SAFE |
| 100 | 0.20 p/m² | 0.02 | 0.01 | SAFE |

#### With 50 people detected:

| area_sqm | Density | Density Norm | Risk (density only) | Approx Level |
|---|---|---|---|---|
| 5 | 10.0 p/m² | 1.00 | 0.40 | CAUTION-WARNING |
| 10 | 5.00 p/m² | 0.50 | 0.20 | CAUTION |
| 20 | 2.50 p/m² | 0.25 | 0.10 | SAFE |
| 50 | 1.00 p/m² | 0.10 | 0.04 | SAFE |
| 100 | 0.50 p/m² | 0.05 | 0.02 | SAFE |

> **Note:** These tables show risk contribution from density alone (40% weight). Actual risk includes velocity (30%) and surge (30%) components plus ML boosts.

### Effect of `expected_capacity` on Capacity Utilization

| People | capacity=30 | capacity=100 | capacity=500 | capacity=2000 |
|---|---|---|---|---|
| 10 | 33% | 10% | 2% | 0.5% |
| 25 | 83% | 25% | 5% | 1.3% |
| 50 | 167% | 50% | 10% | 2.5% |
| 100 | 333% | 100% | 20% | 5% |
| 500 | 1667% | 500% | 100% | 25% |

> **Note:** Capacity utilization is display-only. It does NOT affect risk score, risk level, or alert triggers.

### Combined Risk Examples (Full Formula)

Assuming moderate velocity (0.5 m/s, inv_norm = 0.77) and low surge (0.1, norm = 0.05):

```
base_risk ≈ 0.4 × density_norm + 0.3 × 0.05 + 0.3 × 0.77
          = 0.4 × density_norm + 0.246
```

| People | area=2 | area=3 | area=5 | area=10 | area=50 | area=100 |
|---|---|---|---|---|---|---|
| 5 | 0.35 (C) | 0.31 (C) | 0.29 (C) | 0.27 (C) | 0.25 (C) | 0.25 (S) |
| 10 | 0.45 (C) | 0.38 (C) | 0.33 (C) | 0.29 (C) | 0.25 (C) | 0.25 (S) |
| 15 | 0.55 **(W)** | 0.45 (C) | 0.37 (C) | 0.31 (C) | 0.26 (C) | 0.25 (S) |
| 20 | 0.65 **(W)** | 0.51 **(W)** | 0.41 (C) | 0.33 (C) | 0.26 (C) | 0.25 (S) |
| 25 | 0.75 **(CR)** | 0.58 **(W)** | 0.45 (C) | 0.35 (C) | 0.27 (C) | 0.26 (C) |
| 30 | 0.85 **(CR)** | 0.65 **(W)** | 0.49 (C) | 0.37 (C) | 0.27 (C) | 0.26 (C) |
| 50 | 0.65 **(W)** | 0.65 **(W)** | 0.65 **(W)** | 0.45 (C) | 0.29 (C) | 0.27 (C) |
| 100 | 0.65 **(W)** | 0.65 **(W)** | 0.65 **(W)** | 0.65 **(W)** | 0.33 (C) | 0.29 (C) |

> **Legend:** S = SAFE, C = CAUTION, **(W)** = WARNING (alerts fire), **(CR)** = CRITICAL (alerts fire)
>
> Density norm caps at 1.0 (density >= 10 p/m²), so risk plateaus at ~0.65 from base formula alone. ML boosts (pressure, coherence) and slow velocity can push it above 0.75 into CRITICAL.

---

## 6. Scenario Presets

### Exhibition Demo (max 30 people in video)

| Preset | area_sqm | capacity | WARNING at | CRITICAL at | Best For |
|---|---|---|---|---|---|
| **Aggressive** | 2 | 30 | ~15 people | ~25 people | Impressive live demo |
| **Balanced** | 3 | 30 | ~20 people | ~30 people | Realistic progression |
| **Conservative** | 5 | 30 | ~30 people | Unlikely | Subtle demonstration |

**Recommended for demo: `area_sqm = 2, expected_capacity = 30`**

### Metro Station

| Zone | area_sqm | capacity | WARNING at | CRITICAL at |
|---|---|---|---|---|
| **Platform section** | 75 | 300 | ~450 people | ~560 people |
| **Ticket gate / chokepoint** | 20 | 80 | ~120 people | ~150 people |
| **Staircase / escalator** | 15 | 60 | ~90 people | ~115 people |
| **Main hall / concourse** | 300 | 1000 | ~1800 people | ~2250 people |

### Stadium / Concert

| Zone | area_sqm | capacity | WARNING at | CRITICAL at |
|---|---|---|---|---|
| **Entry gate** | 25 | 100 | ~150 people | ~190 people |
| **Standing section** | 100 | 500 | ~600 people | ~750 people |
| **Exit corridor** | 15 | 50 | ~90 people | ~115 people |
| **Full arena view** | 500 | 5000 | ~3000 people | ~3750 people |

### Religious Gathering / Festival

| Zone | area_sqm | capacity | WARNING at | CRITICAL at |
|---|---|---|---|---|
| **Temple entrance** | 10 | 40 | ~60 people | ~75 people |
| **Main prayer hall** | 200 | 800 | ~1200 people | ~1500 people |
| **Narrow passage** | 8 | 30 | ~48 people | ~60 people |

> **Note:** WARNING/CRITICAL people counts assume moderate velocity (~0.5 m/s) and low surge. Slow-moving or stagnant crowds will trigger alerts at lower counts due to the velocity risk component.

---

## 7. Real-World Density Reference

Based on crowd safety research (Keith Still, Prof. of Crowd Science):

| Density (p/m²) | Condition | Physical Experience | CrowdSafe Level |
|---|---|---|---|
| < 0.5 | Free movement | Full freedom of movement | SAFE |
| 0.5 - 1.0 | Comfortable | Normal walking, can choose path | SAFE |
| 1.0 - 2.0 | Restricted | Reduced speed, awareness of others | SAFE |
| 2.0 - 3.5 | Crowded | Shoulder-to-shoulder, limited path choice | CAUTION |
| 3.5 - 5.0 | Very crowded | Involuntary contact, shuffling | CAUTION-WARNING |
| 5.0 - 6.0 | Dangerous | No voluntary movement possible | WARNING |
| 6.0 - 7.0 | **Critical** | **Breathing restricted, crush force begins** | **WARNING-CRITICAL** |
| 7.0 - 9.0 | **Lethal zone** | **Compressive asphyxia possible** | **CRITICAL** |
| > 9.0 | **Fatal** | **Stampede / crush fatalities** | **CRITICAL** |

### Notable Incidents (Reference)

| Event | Est. Density | Casualties | Year |
|---|---|---|---|
| Mecca Hajj crush | ~9 p/m² | 2,400+ | 2015 |
| Itaewon crowd crush | ~8 p/m² | 159 | 2022 |
| Hillsborough disaster | ~7+ p/m² | 97 | 1989 |
| Love Parade stampede | ~8 p/m² | 21 | 2010 |

> CrowdSafe's default thresholds (WARNING at density ~6, CRITICAL at density ~7+) are calibrated to these real-world safety benchmarks.

---

## Configuration Reference

### Config File (`config.py`)

| Setting | Default | Description |
|---|---|---|
| `RISK_WEIGHT_DENSITY` | 0.4 | Weight for density in risk formula |
| `RISK_WEIGHT_SURGE` | 0.3 | Weight for surge rate in risk formula |
| `RISK_WEIGHT_VELOCITY` | 0.3 | Weight for velocity in risk formula |
| `DENSITY_WARNING` | 6.0 | Density threshold for WARNING level |
| `DENSITY_CRITICAL` | 6.0 | Density threshold for CRITICAL level |
| `VELOCITY_STAGNANT` | 0.2 | Velocity below which crowd is stagnant |
| `ALERT_COOLDOWN` | 60 | Seconds between repeat alerts per camera |
| `YOLO_CONFIDENCE` | 0.25 | YOLO detection confidence threshold |
| `YOLO_MIN_BOX_AREA` | 100 | Minimum bounding box area (pixels) |

### Settings Page (Runtime Adjustable)

Risk thresholds, alert cooldown, and AI confidence can be adjusted live via the Settings page without restarting the server.
