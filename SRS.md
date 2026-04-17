# CrowdSafe - Software Requirements Specification

## Table of Contents

1. [Problem Definition](#1-problem-definition)
2. [Proposed Solution](#2-proposed-solution)
3. [Scope](#3-scope)
4. [Functional Requirements](#4-functional-requirements)
5. [Non-Functional Requirements](#5-non-functional-requirements)
6. [System Features](#6-system-features)
7. [System Architecture](#7-system-architecture)
8. [Database Models](#8-database-models)
9. [API Endpoints](#9-api-endpoints)
10. [Real-Time Events](#10-real-time-events)
11. [Notification Channels](#11-notification-channels)
12. [Configuration Reference](#12-configuration-reference)
13. [Default Data](#13-default-data)
14. [Summary Statistics](#14-summary-statistics)

---

## 1. Problem Definition

Large crowd gatherings at festivals, metro stations, stadiums, and religious events pose severe stampede and crush risks. Manual monitoring fails at scale — by the time a human operator notices dangerous density levels, it is too late to prevent casualties.

### Notable Incidents

| Event | Est. Density | Casualties | Year |
|---|---|---|---|
| Mecca Hajj crush | ~9 p/m² | 2,400+ | 2015 |
| Itaewon crowd crush | ~8 p/m² | 159 | 2022 |
| Hillsborough disaster | ~7+ p/m² | 97 | 1989 |
| Love Parade stampede | ~8 p/m² | 21 | 2010 |

These incidents demonstrate that real-time, automated crowd density monitoring is a critical unsolved need. Current surveillance systems rely on passive CCTV footage reviewed by human operators, which is reactive rather than preventive.

---

## 2. Proposed Solution

**CrowdSafe** is an AI-powered real-time crowd density monitoring and stampede prevention platform that uses:

- **YOLOv11s** computer vision to detect and count people in video feeds
- **BoT-SORT** multi-object tracking to follow individuals across frames
- **ML algorithms** (DBSCAN, z-score, flow coherence, crowd pressure) to analyze crowd behavior
- **Multi-factor risk scoring** to quantify danger levels in real-time
- **Multi-channel alerting** (Telegram, SocketIO, dashboard) to notify operators before dangerous conditions develop
- **Professional CCTV-style annotations** for intuitive visual monitoring

The system is designed to transition crowd safety from reactive to preventive by providing early warnings at WARNING (50-74% risk) and CRITICAL (75-100% risk) levels.

---

## 3. Scope

| # | Scope Item |
|---|---|
| S1 | Real-time person detection and tracking from video feeds (uploaded or RTSP) |
| S2 | Crowd density calculation and risk scoring using multi-factor weighted formula |
| S3 | ML-based crowd behavior analysis (clustering, flow coherence, pressure, anomalies) |
| S4 | Automated alert generation with cooldown and escalation |
| S5 | Multi-channel notifications (Telegram with photo, SocketIO real-time, dashboard) |
| S6 | Live annotated MJPEG video streaming with professional CCTV-style overlays |
| S7 | Historical data storage, querying, and time-series analytics |
| S8 | Data export in 4 formats (CSV, DOCX, PDF, Markdown) |
| S9 | Role-based user management (admin/operator/viewer) |
| S10 | Configurable thresholds and AI parameters via settings UI |
| S11 | Recording of analyzed video sessions for playback |
| S12 | Density heatmap overlay visualization |

**Total: 12 scope items**

---

## 4. Functional Requirements

| ID | Requirement |
|---|---|
| FR1 | System shall detect and count people in video frames using YOLOv11s object detection |
| FR2 | System shall track individuals across frames using BoT-SORT with persistent track IDs |
| FR3 | System shall calculate crowd density as `people_count / area_sqm` (persons per m²) |
| FR4 | System shall compute risk score using weighted formula: 40% density + 30% surge + 30% velocity + ML boosts |
| FR5 | System shall classify risk into 4 levels: SAFE (0-24%), CAUTION (25-49%), WARNING (50-74%), CRITICAL (75-100%) |
| FR6 | System shall generate alerts when risk reaches WARNING or CRITICAL with 60-second cooldown per camera |
| FR7 | System shall send Telegram notifications with annotated frame snapshot on alert |
| FR8 | System shall stream live annotated video via MJPEG with bounding boxes, HUD panel, and sparkline |
| FR9 | System shall perform DBSCAN spatial clustering to detect crowd groups |
| FR10 | System shall detect velocity anomalies using z-score analysis (threshold: 2.0) |
| FR11 | System shall calculate flow coherence (0-1) as stampede indicator |
| FR12 | System shall estimate crowd pressure from nearest-neighbor distance + velocity variance |
| FR13 | System shall predict density/risk trends using exponential moving average |
| FR14 | System shall support date-range filtering on analytics (1H, 24H, 7D, 30D, All, Custom) |
| FR15 | System shall export metrics data in CSV, DOCX, PDF, and Markdown formats |
| FR16 | System shall authenticate users via JWT (access + refresh tokens) with bcrypt password hashing |
| FR17 | System shall support 3 user roles: admin (full access), operator (monitoring), viewer (read-only) |
| FR18 | System shall allow runtime configuration of risk thresholds, AI confidence, and alert settings |
| FR19 | System shall record annotated video sessions as MP4 for later download |
| FR20 | System shall display density heatmap overlay on video stream when toggled |

**Total: 20 functional requirements**

---

## 5. Non-Functional Requirements

| ID | Requirement |
|---|---|
| NFR1 | System shall process video at 15 FPS with frame skip of 2 for real-time performance |
| NFR2 | System shall use SQLite for zero-configuration database deployment |
| NFR3 | System shall run on a single machine without external service dependencies (except optional Telegram) |
| NFR4 | System shall use threading mode for SocketIO (no eventlet/gevent dependency) |
| NFR5 | All timestamps shall be stored in UTC and displayed in IST (UTC+5:30) to the user |
| NFR6 | System shall persist metrics every 10 frames to balance storage vs. granularity |
| NFR7 | Alert notifications shall be sent in background threads to avoid blocking the video pipeline |
| NFR8 | YOLO input shall be resized to max 960px for GPU/CPU performance optimization |
| NFR9 | System shall auto-clean metrics older than 30 days and logs older than 90 days |
| NFR10 | Frontend shall use dark theme (bg #111318, accent #4f8ff7) with Bootstrap 5.3 |
| NFR11 | All API endpoints shall require JWT authentication (except login and health check) |
| NFR12 | Export service shall handle up to 5,000 records per export without timeout |

**Total: 12 non-functional requirements**

---

## 6. System Features

### SF1. AI Person Detection

- YOLOv11s deep learning model (pre-trained on COCO dataset, class 0: person)
- BoT-SORT multi-object tracking with Kalman filtering
- Confidence threshold filtering (default: 0.25)
- IOU threshold filtering (default: 0.5)
- Minimum bounding box area filter (100px)
- Maximum aspect ratio filter (5.0)
- Dense crowd grid estimation with occlusion factor (1.3x) for 50+ people

### SF2. Crowd Behavior Analysis (ML Layer)

| Algorithm | Purpose | Output |
|---|---|---|
| DBSCAN Clustering | Detect crowd groups | Cluster count, centers, sizes |
| Proximity Analysis | Social distance monitoring | Pair alerts with distances |
| Velocity Anomaly (z-score) | Detect abnormal movement | Fast movers / stationary flagged |
| Flow Coherence | Stampede indicator | 0.0 (random) to 1.0 (stampede) |
| Crowd Pressure | Crush risk estimation | 0.0 (safe) to 1.0 (dangerous) |
| EMA Trend Prediction | Forecast density/risk direction | Increasing / Stable / Decreasing |

### SF3. Risk Scoring Engine

```
Base Score = (0.4 x density_norm) + (0.3 x surge_norm) + (0.3 x velocity_inv_norm)

ML Boosts:
  + max(0, pressure - 0.3) x 0.15    (max +0.105)
  + max(0, coherence - 0.5) x 0.2    (max +0.10)
  x 1.15 if count > 100              (large crowd multiplier)

Final Risk = clamp(Base + Boosts, 0.0, 1.0)
```

| Level | Score Range | Color | Action |
|---|---|---|---|
| SAFE | 0% - 24% | Green | Normal monitoring |
| CAUTION | 25% - 49% | Yellow | Increased attention |
| WARNING | 50% - 74% | Orange | Alert triggered, Telegram sent |
| CRITICAL | 75% - 100% | Red | Immediate action, Telegram sent |

### SF4. Alert System

- Threshold detection at WARNING and CRITICAL levels
- 60-second cooldown per camera per risk level
- 4 trigger condition types:
  - `extreme_density`: density > 6.0 p/m²
  - `sudden_surge`: surge_rate > 0.8
  - `stagnation_with_density`: velocity < 0.2 m/s AND density > 4.0
  - `risk_threshold`: general risk level breach (fallback)
- Database persistence with acknowledge/resolve workflow
- Multi-channel dispatch (SocketIO + Telegram)

### SF5. Telegram Notifications

- Zero-dependency implementation (Python stdlib urllib only)
- Photo attachment with annotated crowd frame
- Rich caption with: risk level, camera name/location, trigger, all metrics
- IST formatted timestamps
- Background thread execution (non-blocking)
- Configurable bot token and chat ID via settings UI

### SF6. Live Video Streaming

- MJPEG format (multipart/x-mixed-replace)
- 15 FPS stream rate
- 6-layer professional annotation system:
  1. Cluster outlines (convex hull)
  2. Proximity warning circles
  3. Flow direction arrows
  4. Per-person corner-style bounding boxes with ID + confidence
  5. HUD panel (top-left stats overlay)
  6. Sparkline chart (density + risk history)

### SF7. Density Heatmap

- Gaussian blob accumulation at person center points
- JET colormap (blue = low density, red = high density)
- Toggleable overlay via URL parameter (`?heatmap=1`)
- Toggle button on camera view page

### SF8. Analytics Dashboard

- 4 time-series line charts (Person Count, Density, Risk Score, Velocity)
- 6 summary statistic cards (Avg People, Peak Count, Avg/Max Density, Max/Avg Risk, Avg Velocity, Total Records)
- Time range presets: 1 Hour, 24 Hours, 7 Days, 30 Days, All Time
- Custom date range picker with Apply button
- Collapsible raw data table with color-coded risk badges
- All timestamps displayed in IST

### SF9. Data Export

| Format | Library | Features |
|---|---|---|
| CSV | Python stdlib `csv` | Tabular data with all metric fields |
| DOCX | `python-docx` | Professional report with summary table + data table |
| PDF | `fpdf2` | Color-coded risk levels, formatted layout |
| Markdown | Python stdlib | GitHub-compatible tables |

All exports include: camera name, IST timestamps, summary statistics, full metrics data.

### SF10. User Management

- JWT authentication (HS256) with access + refresh tokens
- bcrypt password hashing (12 rounds)
- 3 roles: admin (full), operator (monitoring), viewer (read-only)
- CRUD operations for user accounts
- Password reset functionality
- Last login tracking

### SF11. Settings Management

| Section | Configurable Parameters |
|---|---|
| Risk Thresholds | Density warning/critical, velocity stagnant, risk weights |
| Alert Configuration | Cooldown seconds, Telegram enable/disable, bot token, chat ID |
| AI Settings | YOLO model, confidence threshold, IOU threshold |

All settings adjustable at runtime via UI without server restart.

### SF12. Video Recording

- Automatic recording during AI processing
- Annotated frames saved as MP4
- Recording metadata stored in database (duration, frame count, file size)
- Download via API endpoint
- Recording ID returned on processing stop

### SF13. Real-Time Updates (SocketIO)

- Live metrics broadcast (per-camera rooms + global)
- Alert notifications with toast messages
- Camera status change events
- Dashboard auto-refresh (5-second interval + event-driven)
- WebSocket connection status indicator

### SF14. Camera Management

- Multi-camera registry (singleton pattern)
- Video file upload with XHR progress tracking
- Shared AI engine instance across all cameras
- Start/stop processing per camera
- Camera metadata: name, location, area (m²), expected capacity, GPS coordinates

### SF15. System Monitoring

- Health check endpoint (`/api/system/health`)
- System statistics (camera count, alert count, metrics recorded)
- Log viewer with level and component filtering
- Scheduled cleanup of old metrics (30 days) and logs (90 days)

**Total: 15 system features**

---

## 7. System Architecture

### Technology Stack

| Layer | Technology |
|---|---|
| Backend Framework | Flask 3.x |
| Database | SQLite (via SQLAlchemy ORM) |
| Real-Time | Flask-SocketIO (threading mode) |
| AI/ML Model | YOLOv11s (Ultralytics) |
| Object Tracking | BoT-SORT |
| ML Analysis | scikit-learn (DBSCAN), NumPy |
| Frontend | Jinja2 templates, Bootstrap 5.3 (dark theme) |
| Charts | Chart.js 4.4.7 |
| Authentication | PyJWT + bcrypt |
| Notifications | Telegram Bot API (urllib) |
| Export | python-docx, fpdf2, csv (stdlib) |
| Video Processing | OpenCV (headless) |

### Pipeline Flow

```
Video Input
    |
    v
VideoProcessor (background thread)
    |
    v
ai_engine.analyze_frame()
    |-- YOLO detection + BoT-SORT tracking
    |-- Velocity calculation from track history
    |
    v
crowd_analyzer.analyze()
    |-- DBSCAN clustering
    |-- Proximity analysis
    |-- Velocity anomaly detection
    |-- Flow coherence calculation
    |-- Crowd pressure estimation
    |-- EMA trend prediction
    |
    v
risk_calculator.calculate()
    |-- Weighted base score
    |-- ML boost (pressure + coherence)
    |-- Risk level classification
    |
    v
ai_engine.annotate_frame()
    |-- 6-layer annotation rendering
    |-- Optional heatmap overlay
    |
    v
Output
    |-- MJPEG stream to frontend
    |-- Metrics to DB (every 10 frames)
    |-- Metrics via SocketIO (every frame)
    |-- Alert check (WARNING/CRITICAL -> DB + Telegram)
    |-- Recording to MP4
```

### Key Files

| File | Purpose |
|---|---|
| `app.py` | Application entry point |
| `config.py` | All configuration and thresholds |
| `backend/__init__.py` | App factory, blueprint registration, defaults |
| `backend/services/ai_engine.py` | YOLO + BoT-SORT + annotation rendering |
| `backend/services/crowd_analyzer.py` | ML analysis layer |
| `backend/services/risk_calculator.py` | Multi-factor risk scoring |
| `backend/services/video_processor.py` | Background thread, MJPEG stream, orchestration |
| `backend/services/camera_manager.py` | Singleton camera registry |
| `backend/services/alert_manager.py` | Alert creation, cooldown, dispatch |
| `backend/services/telegram_service.py` | Telegram Bot API integration |
| `backend/services/export_service.py` | CSV/DOCX/PDF/MD generation |

---

## 8. Database Models

### User

| Field | Type | Description |
|---|---|---|
| id | Integer (PK) | Auto-increment |
| username | String(50), unique | Login identifier |
| email | String(120), unique | Email address |
| password_hash | String(255) | bcrypt hashed password |
| full_name | String(100) | Display name |
| role | String(20) | admin / operator / viewer |
| is_active | Boolean | Account enabled flag |
| phone | String(20) | Contact number |
| created_at | DateTime | Account creation (UTC) |
| last_login | DateTime | Last login timestamp (UTC) |

### Camera

| Field | Type | Description |
|---|---|---|
| id | String (PK) | UUID-based identifier |
| name | String(100) | Display name |
| location | String(200) | Physical location description |
| source_type | String(20) | rtsp / http / file / usb |
| source_url | String(500) | Video source path or URL |
| area_sqm | Float | Physical area covered (m²) |
| expected_capacity | Integer | Max expected people count |
| calibration_method | String(20) | aruco / manual / reference |
| calibration_data | Text (JSON) | Calibration parameters |
| roi | Text (JSON) | Region of Interest definition |
| is_active | Boolean | Camera enabled flag |
| status | String(20) | online / offline / error / processing |
| latitude, longitude | Float | GPS coordinates |
| fps_target | Integer | Target processing FPS |
| resolution | String(20) | Video resolution |
| created_at, updated_at | DateTime | Timestamps (UTC) |

### Metric

| Field | Type | Description |
|---|---|---|
| id | Integer (PK) | Auto-increment |
| camera_id | String (FK) | Camera reference |
| timestamp | DateTime (indexed) | Measurement time (UTC) |
| count | Integer | People detected |
| density | Float | People per m² |
| avg_velocity | Float | Average movement speed (m/s) |
| max_velocity | Float | Maximum movement speed (m/s) |
| surge_rate | Float | Rate of count increase |
| flow_in, flow_out | Integer | Directional flow counts |
| risk_score | Float | 0.0 - 1.0 risk value |
| risk_level | String(20) | SAFE / CAUTION / WARNING / CRITICAL |
| capacity_utilization | Float | Percentage of expected capacity |
| frame_number | Integer | Source frame index |

### Alert

| Field | Type | Description |
|---|---|---|
| id | Integer (PK) | Auto-increment |
| alert_id | String(50), unique | Human-readable identifier |
| camera_id | String (FK, indexed) | Camera reference |
| timestamp | DateTime (indexed) | Alert time (UTC) |
| risk_level | String(20) | WARNING / CRITICAL |
| trigger_condition | String(100) | What triggered the alert |
| message | Text | Human-readable alert message |
| metrics_snapshot | Text (JSON) | Full metrics at alert time |
| acknowledged | Boolean | Operator acknowledged |
| acknowledged_by | Integer (FK) | User who acknowledged |
| acknowledged_at | DateTime | Acknowledgement time |
| resolved | Boolean | Alert resolved |
| resolved_at | DateTime | Resolution time |
| snapshot_path | String(255) | Frame image file path |

### Recording

| Field | Type | Description |
|---|---|---|
| id | Integer (PK) | Auto-increment |
| recording_id | String, unique | Human-readable identifier |
| camera_id | String (FK, indexed) | Camera reference |
| filename, filepath | String | File information |
| start_time, end_time | DateTime | Recording duration |
| duration_seconds | Float | Length in seconds |
| frame_count | Integer | Total frames recorded |
| width, height | Integer | Video resolution |
| fps | Float | Recording frame rate |
| file_size_bytes | BigInteger | File size |
| thumbnail_path | String | Preview image path |
| trigger_type | String | manual / alert / scheduled |

### Setting

| Field | Type | Description |
|---|---|---|
| id | Integer (PK) | Auto-increment |
| key | String, unique | Setting identifier |
| value | Text | Setting value |
| category | String | general / risk / alerts / ai |
| description | Text | Human-readable description |
| updated_at | DateTime | Last update time |
| updated_by | Integer (FK) | User who updated |

### SystemLog

| Field | Type | Description |
|---|---|---|
| id | Integer (PK) | Auto-increment |
| timestamp | DateTime (indexed) | Log time (UTC) |
| level | String (indexed) | info / warning / error |
| component | String | Source module |
| message | Text | Log message |
| details | Text (JSON) | Additional data |
| user_id | Integer (FK) | Associated user |

---

## 9. API Endpoints

### Authentication (`/api/auth`) — 4 endpoints

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/auth/login` | User login, returns JWT tokens |
| POST | `/api/auth/logout` | User logout |
| POST | `/api/auth/refresh` | Refresh access token |
| GET | `/api/auth/me` | Get current user info |

### Cameras (`/api/cameras`) — 9 endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/cameras` | List all cameras with status |
| POST | `/api/cameras` | Create new camera |
| GET | `/api/cameras/{id}` | Get camera details |
| PUT | `/api/cameras/{id}` | Update camera settings |
| DELETE | `/api/cameras/{id}` | Delete camera |
| POST | `/api/cameras/{id}/upload` | Upload video file |
| POST | `/api/cameras/{id}/start` | Start AI processing |
| POST | `/api/cameras/{id}/stop` | Stop AI processing |
| GET | `/api/cameras/{id}/stream` | MJPEG video stream |

### Metrics (`/api/metrics`) — 6 endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/metrics/{id}` | Get metrics (filterable by date range) |
| GET | `/api/metrics/{id}/current` | Get latest live metrics |
| GET | `/api/metrics/{id}/summary` | Statistical summary |
| GET | `/api/metrics/{id}/aggregate` | Time-bucketed aggregates |
| GET | `/api/metrics/{id}/export` | Export as CSV/DOCX/PDF/MD |
| GET | `/api/metrics/summary` | Global summary across all cameras |

### Alerts (`/api/alerts`) — 5 endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/alerts` | List alerts (filterable) |
| GET | `/api/alerts/{id}` | Get alert details |
| POST | `/api/alerts/{id}/acknowledge` | Acknowledge alert |
| POST | `/api/alerts/{id}/resolve` | Resolve alert |
| GET | `/api/alerts/unacknowledged/count` | Count open alerts |

### Recordings (`/api/recordings`) — 4 endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/recordings` | List recordings |
| GET | `/api/recordings/{id}` | Get recording details |
| GET | `/api/recordings/{id}/download` | Download recording file |
| DELETE | `/api/recordings/{id}` | Delete recording |

### Settings (`/api/settings`) — 3 endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/settings/{category}` | Get settings by category |
| PUT | `/api/settings/{category}/{key}` | Update a setting |
| POST | `/api/settings/risk-thresholds` | Bulk update risk thresholds |

### Users (`/api/users`) — 5 endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/users` | List all users |
| POST | `/api/users` | Create new user |
| PUT | `/api/users/{id}` | Update user |
| DELETE | `/api/users/{id}` | Delete user |
| POST | `/api/users/{id}/reset-password` | Reset password |

### System (`/api/system`) — 3 endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/system/health` | Health check |
| GET | `/api/system/stats` | System statistics |
| GET | `/api/system/logs` | View system logs |

**Total: 39 API endpoints**

---

## 10. Real-Time Events (SocketIO)

### Client to Server

| Event | Payload | Description |
|---|---|---|
| `subscribe_camera` | `{camera_id}` | Join camera-specific room |
| `unsubscribe_camera` | `{camera_id}` | Leave camera-specific room |
| `get_metrics` | `{camera_id}` | Request latest metrics |

### Server to Client

| Event | Payload | Description |
|---|---|---|
| `metrics_update` | Full metrics object | Real-time metrics broadcast |
| `alert` | Alert object | New alert notification |
| `camera_status` | `{camera_id, status}` | Camera status change |
| `system_notification` | `{type, message}` | System messages |

---

## 11. Notification Channels

| Channel | Status | Trigger Level | Details |
|---|---|---|---|
| Dashboard (SocketIO) | Active | WARNING, CRITICAL | Toast notifications, alert badge, live metrics |
| Telegram Bot | Active | WARNING, CRITICAL | Photo + caption with full metrics, IST timestamps |
| Email (SMTP) | Configured, not implemented | - | Toggle exists in settings |
| SMS (Twilio) | Configured, not implemented | - | Toggle exists in settings |

---

## 12. Configuration Reference

### AI / Detection

| Parameter | Default | Description |
|---|---|---|
| `YOLO_MODEL` | yolo11s.pt | YOLO model file |
| `YOLO_CONFIDENCE` | 0.25 | Detection confidence threshold |
| `YOLO_IOU` | 0.5 | IOU threshold |
| `YOLO_IMGSZ` | 960 | Input image size (px) |
| `YOLO_MIN_BOX_AREA` | 100 | Minimum bounding box area (px) |
| `YOLO_MAX_BOX_RATIO` | 5.0 | Maximum aspect ratio filter |

### ML / Crowd Analysis

| Parameter | Default | Description |
|---|---|---|
| `PROXIMITY_THRESHOLD_PX` | 80 | Proximity alert distance (px) |
| `CLUSTER_EPS_PX` | 120 | DBSCAN epsilon (px) |
| `CLUSTER_MIN_SAMPLES` | 2 | DBSCAN minimum cluster size |
| `ANOMALY_VELOCITY_ZSCORE` | 2.0 | Z-score threshold for anomaly |
| `COHERENCE_WINDOW` | 10 | Flow coherence window (frames) |

### Risk Scoring

| Parameter | Default | Description |
|---|---|---|
| `RISK_WEIGHT_DENSITY` | 0.4 | Density weight in formula |
| `RISK_WEIGHT_SURGE` | 0.3 | Surge rate weight |
| `RISK_WEIGHT_VELOCITY` | 0.3 | Velocity weight |
| `DENSITY_WARNING` | 6.0 | Density for WARNING level |
| `DENSITY_CRITICAL` | 6.0 | Density for CRITICAL level |
| `VELOCITY_STAGNANT` | 0.2 | Stagnant velocity threshold (m/s) |
| `RISK_WARNING` | 0.50 | Risk score for WARNING |
| `RISK_CRITICAL` | 0.75 | Risk score for CRITICAL |

### Processing

| Parameter | Default | Description |
|---|---|---|
| `PROCESS_FPS` | 15 | Target processing frame rate |
| `FRAME_SKIP` | 2 | Process every Nth frame |
| `DENSE_CROWD_THRESHOLD` | 50 | Switch to grid estimation |
| `OCCLUSION_FACTOR` | 1.3 | Dense crowd count multiplier |

### Alerts

| Parameter | Default | Description |
|---|---|---|
| `ALERT_COOLDOWN` | 60 | Seconds between repeat alerts |

### Server

| Parameter | Default | Description |
|---|---|---|
| `HOST` | 0.0.0.0 | Bind address |
| `PORT` | 5001 | Server port |

---

## 13. Default Data

### Default Admin Account

| Field | Value |
|---|---|
| Username | admin |
| Password | admin123 |
| Email | admin@crowdsafe.local |
| Role | admin |

### Default Settings

| Category | Key | Default Value |
|---|---|---|
| general | app_name | CrowdSafe |
| general | timezone | UTC |
| general | theme | dark |
| risk | density_warning | 4.0 |
| risk | density_critical | 6.0 |
| risk | velocity_stagnant | 0.2 |
| risk | weight_density | 0.4 |
| risk | weight_surge | 0.3 |
| risk | weight_velocity | 0.3 |
| alerts | cooldown_seconds | 60 |
| alerts | email_enabled | false |
| alerts | sms_enabled | false |
| alerts | telegram_enabled | true |
| ai | model | yolo11n.pt |
| ai | confidence | 0.5 |
| ai | iou | 0.7 |

---

## 14. Summary Statistics

| Category | Count |
|---|---|
| Scope Items | 12 |
| Functional Requirements | 20 |
| Non-Functional Requirements | 12 |
| System Features | 15 |
| API Endpoints | 39 |
| Database Models | 7 |
| Backend Services | 9 |
| Frontend Pages | 7 |
| SocketIO Events | 7 |
| Export Formats | 4 |
| Notification Channels | 4 |
| Configuration Options | 40+ |
| ML Algorithms | 6 |
| Annotation Layers | 6 |
