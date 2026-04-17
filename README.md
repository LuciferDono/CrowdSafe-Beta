<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/Flask-3.1-000000?style=for-the-badge&logo=flask&logoColor=white" alt="Flask">
  <img src="https://img.shields.io/badge/YOLOv11s-Ultralytics-00FFFF?style=for-the-badge&logo=yolo&logoColor=black" alt="YOLO">
  <img src="https://img.shields.io/badge/OpenCV-4.10-5C3EE8?style=for-the-badge&logo=opencv&logoColor=white" alt="OpenCV">
  <img src="https://img.shields.io/badge/Bootstrap-5.3-7952B3?style=for-the-badge&logo=bootstrap&logoColor=white" alt="Bootstrap">
  <img src="https://img.shields.io/badge/Docker-Ready-2496ED?style=for-the-badge&logo=docker&logoColor=white" alt="Docker">
</p>

# CrowdSafe

**AI-powered crowd density monitoring and stampede prevention platform.**

CrowdSafe uses real-time computer vision and machine learning to detect dangerous crowd conditions — high density, sudden surges, flow disruptions, and crushing pressure — and sends alerts before situations escalate.

---

## Table of Contents

- [Features](#features)
- [Architecture](#architecture)
- [Tech Stack](#tech-stack)
- [Getting Started](#getting-started)
- [Configuration](#configuration)
- [API Reference](#api-reference)
- [ML Pipeline](#ml-pipeline)
- [Risk Scoring](#risk-scoring)
- [Screenshots](#screenshots)
- [Project Structure](#project-structure)
- [License](#license)

---

## Features

### Real-Time AI Analysis
- **YOLOv11s person detection** with BoT-SORT multi-object tracking
- **DBSCAN spatial clustering** to identify congestion zones
- **Velocity anomaly detection** using z-score outlier analysis
- **Flow coherence measurement** — detects crowd panic (uniform vs. chaotic movement)
- **Crowd pressure estimation** — crush risk from density + velocity variance
- **EMA trend prediction** for density and risk forecasting

### Professional Video Overlay
- Corner-style CCTV bounding boxes with track IDs and velocity
- Cluster convex hull outlines
- Proximity warning circles for social distancing violations
- Flow direction arrows per person
- Velocity trail history (fading)
- Real-time HUD with people count, density, risk level, clusters, and sparkline charts
- Gaussian density heatmap overlay

### Alert System
- Automatic risk-level alerts (WARNING, CRITICAL) with configurable cooldowns
- Trigger conditions: density threshold, sudden surge, stagnation + high density
- **Telegram notifications** with frame snapshots and metrics
- Alert acknowledgement and resolution workflow

### Analytics & Export
- Historical time-series charts (count, density, risk, velocity)
- Date range filtering with quick presets (1H, 24H, 7D, 30D)
- Time-bucketed aggregation (hourly / daily / weekly)
- Export to **CSV, DOCX, PDF, Markdown**
- Collapsible raw data table

### Platform
- JWT authentication with role-based access (admin, operator, viewer)
- Real-time WebSocket updates via Socket.IO
- Camera management with RTSP, HTTP, USB, and video file support
- Automatic recording of analyzed video
- Dark theme UI with left sidebar navigation
- Docker + Nginx deployment ready

---

## Architecture

```
                         ┌─────────────────────────────────────────────┐
                         │              Frontend (Browser)              │
                         │  Bootstrap 5.3 + Chart.js + Socket.IO       │
                         └──────────┬──────────────┬───────────────────┘
                                    │ REST API      │ WebSocket
                         ┌──────────▼──────────────▼───────────────────┐
                         │           Flask Application                  │
                         │  ┌─────────────┐  ┌──────────────────────┐  │
                         │  │  API Routes  │  │  WebSocket Events    │  │
                         │  │  (Blueprints)│  │  (Flask-SocketIO)    │  │
                         │  └──────┬──────┘  └──────────┬───────────┘  │
                         │         │                     │              │
                         │  ┌──────▼─────────────────────▼───────────┐ │
                         │  │           Service Layer                 │ │
                         │  │                                         │ │
                         │  │  ┌──────────────┐  ┌────────────────┐  │ │
                         │  │  │ CameraManager│  │  AlertManager  │  │ │
                         │  │  │  (Singleton) │  │  + Telegram    │  │ │
                         │  │  └──────┬───────┘  └────────────────┘  │ │
                         │  │         │                               │ │
                         │  │  ┌──────▼───────┐                      │ │
                         │  │  │VideoProcessor│  (Background Thread)  │ │
                         │  │  └──────┬───────┘                      │ │
                         │  │         │                               │ │
                         │  │  ┌──────▼───────┐  ┌────────────────┐  │ │
                         │  │  │   AIEngine   │──│ CrowdAnalyzer  │  │ │
                         │  │  │  YOLOv11s +  │  │ DBSCAN, Flow,  │  │ │
                         │  │  │  BoT-SORT    │  │ Pressure, EMA  │  │ │
                         │  │  └──────┬───────┘  └───────┬────────┘  │ │
                         │  │         │                   │           │ │
                         │  │  ┌──────▼───────────────────▼────────┐ │ │
                         │  │  │         RiskCalculator             │ │ │
                         │  │  │  Weighted Score + ML Boosts        │ │ │
                         │  │  └───────────────────────────────────┘ │ │
                         │  └─────────────────────────────────────────┘ │
                         │                                              │
                         │  ┌──────────────────────────────────────┐   │
                         │  │  SQLite (Metrics, Alerts, Cameras,   │   │
                         │  │  Users, Recordings, Settings, Logs)  │   │
                         │  └──────────────────────────────────────┘   │
                         └─────────────────────────────────────────────┘
```

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| **Backend** | Flask 3.1, SQLAlchemy, Flask-SocketIO |
| **AI/ML** | YOLOv11s (Ultralytics), BoT-SORT, scikit-learn (DBSCAN) |
| **Computer Vision** | OpenCV 4.10, Pillow |
| **Frontend** | Jinja2, Bootstrap 5.3, Chart.js, Socket.IO |
| **Database** | SQLite |
| **Auth** | JWT (PyJWT) + bcrypt |
| **Notifications** | Telegram Bot API |
| **Export** | python-docx, fpdf2, csv (stdlib) |
| **Deployment** | Docker, Gunicorn, Nginx |

---

## Getting Started

### Prerequisites

- Python 3.11+
- pip
- (Optional) Docker & Docker Compose

### Local Setup

```bash
# Clone the repository
git clone https://github.com/LuciferDono/CrowdSafe.git
cd CrowdSafe

# Create virtual environment
python -m venv venv
source venv/bin/activate        # Linux/macOS
venv\Scripts\activate           # Windows

# Install dependencies
pip install -r requirements.txt

# Configure environment (optional)
cp .env.example .env
# Edit .env with your settings

# Run the application
python app.py
```

The app starts at **http://localhost:5001**

**Default login:** `admin` / `admin123`

### Docker Setup

```bash
docker-compose up --build
```

Access via **http://localhost** (Nginx proxies to the app).

---

## Configuration

All thresholds are configurable via `config.py` or environment variables.

### Detection

| Parameter | Default | Description |
|-----------|---------|-------------|
| `YOLO_MODEL` | `yolo11s.pt` | YOLO model variant |
| `YOLO_CONFIDENCE` | `0.25` | Detection confidence threshold |
| `YOLO_IOU` | `0.5` | NMS IoU threshold |
| `YOLO_IMGSZ` | `960` | Input image size (px) |

### Risk Thresholds

| Level | Density (p/m^2) | Risk Score |
|-------|-----------------|------------|
| SAFE | 0 - 2.0 | 0% - 25% |
| CAUTION | 2.0 - 4.0 | 25% - 50% |
| WARNING | 4.0 - 6.0 | 50% - 75% |
| CRITICAL | > 6.0 | 75% - 100% |

### ML Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `CLUSTER_EPS_PX` | `120` | DBSCAN neighborhood radius |
| `CLUSTER_MIN_SAMPLES` | `2` | Min points for cluster |
| `ANOMALY_VELOCITY_ZSCORE` | `2.0` | Velocity outlier threshold |
| `COHERENCE_WINDOW` | `10` | Flow history buffer (frames) |
| `PROXIMITY_THRESHOLD_PX` | `80` | Social distance threshold |

### Telegram Alerts

Telegram is **disabled by default** — no credentials ship with the repo. You must create your own bot and wire it up after cloning.

#### 1. Create a bot

Open Telegram, message [@BotFather](https://t.me/BotFather):

```
/newbot
```

Follow the prompts. BotFather returns a token like `123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11`. **Keep it secret.**

#### 2. Get your chat ID

- **Personal DM:** Send any message to your new bot first, then visit:
  ```
  https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates
  ```
  Look for `"chat":{"id": 123456789, ...}` — that's your chat ID.

- **Group / channel:** Add the bot to the group, send a message, then hit the same URL. The ID will be negative (e.g., `-1001234567890`). For channels, the bot needs admin rights.

#### 3. Wire it up (pick one)

**Option A — `.env` file** (preferred for self-hosted / Docker):

```bash
cp .env.example .env
# edit .env and fill in:
TELEGRAM_BOT_TOKEN=123456:ABC-your-actual-token
TELEGRAM_CHAT_ID=-1001234567890
```

**Option B — Settings UI** (preferred for non-devs):

1. Run the app and log in as `admin`
2. Navigate to **Settings -> Alerts**
3. Paste the bot token and chat ID, save

Values entered via the UI are stored in the database and **override** `.env` values, so UI edits always win.

#### 4. Verify

Trigger a WARNING or CRITICAL alert (upload a dense-crowd test video). Check the `logs/` directory — you should see `Telegram alert sent: <id>`. If credentials are blank or missing, the alert manager silently skips the Telegram send (app keeps running normally).

---

## API Reference

### Authentication
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/login` | Login (returns JWT) |
| POST | `/api/auth/logout` | Logout |
| POST | `/api/auth/refresh` | Refresh token |
| GET | `/api/auth/me` | Current user profile |

### Cameras
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/cameras/` | List all cameras |
| POST | `/api/cameras/` | Create camera |
| GET | `/api/cameras/<id>` | Camera details + live metrics |
| PUT | `/api/cameras/<id>` | Update camera |
| DELETE | `/api/cameras/<id>` | Delete camera |
| POST | `/api/cameras/<id>/upload` | Upload video for analysis |
| GET | `/api/cameras/<id>/stream` | MJPEG video stream |

### Metrics
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/metrics/<cam_id>` | Historical metrics (with date filter) |
| GET | `/api/metrics/<cam_id>/current` | Latest live metrics |
| GET | `/api/metrics/<cam_id>/summary` | Aggregated statistics |
| GET | `/api/metrics/<cam_id>/aggregate` | Time-bucketed data |
| GET | `/api/metrics/<cam_id>/export` | Export (CSV/DOCX/PDF/MD) |

### Alerts
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/alerts/` | List alerts (filterable) |
| GET | `/api/alerts/<id>` | Alert details |
| POST | `/api/alerts/<id>/acknowledge` | Acknowledge alert |
| POST | `/api/alerts/<id>/resolve` | Resolve alert |
| GET | `/api/alerts/unacknowledged/count` | Unacknowledged count |
| GET | `/api/alerts/statistics` | Stats by risk level |

### System
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/system/health` | Health check |
| GET | `/api/system/stats` | System statistics |
| GET | `/api/system/logs` | Application logs |

---

## ML Pipeline

```
Video Frame
    │
    ▼
┌─────────────────┐
│  YOLOv11s       │  Person detection (conf > 0.25)
│  Detection      │  Filters: min area, max aspect ratio
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  BoT-SORT       │  Kalman filter + appearance matching
│  Tracking       │  Assigns persistent track IDs
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Per-Person      │  Position, velocity, direction
│  Metrics         │  Track history (60-frame buffer)
└────────┬────────┘
         │
    ┌────┴────┬────────────┬──────────────┐
    ▼         ▼            ▼              ▼
┌────────┐ ┌─────────┐ ┌───────────┐ ┌──────────┐
│ DBSCAN │ │Velocity │ │  Flow     │ │  Crowd   │
│Cluster │ │Anomaly  │ │Coherence  │ │ Pressure │
│Analysis│ │Detection│ │ Analysis  │ │Estimation│
└───┬────┘ └────┬────┘ └─────┬─────┘ └────┬─────┘
    │           │             │             │
    └─────┬─────┴─────────────┴─────────────┘
          ▼
   ┌──────────────┐
   │    Risk       │  Weighted: 40% density + 30% surge + 30% velocity
   │  Calculator   │  ML boosts: pressure + coherence
   └──────┬───────┘
          │
          ▼
   ┌──────────────┐
   │  EMA Trend   │  Exponential moving average (alpha=0.3)
   │  Prediction  │  Predicts density and risk trend
   └──────────────┘
```

### Algorithms

| Algorithm | Purpose | Key Parameters |
|-----------|---------|---------------|
| **YOLOv11s** | Real-time person detection | conf=0.25, iou=0.5, imgsz=960 |
| **BoT-SORT** | Multi-object tracking with re-identification | Kalman filter + appearance |
| **DBSCAN** | Spatial clustering of detected people | eps=120px, min_samples=2 |
| **Z-Score** | Velocity anomaly detection | threshold=2.0 std deviations |
| **Flow Coherence** | Magnitude of mean direction vector | 0=chaotic, 1=uniform flow |
| **Crowd Pressure** | 0.6 * density_pressure + 0.4 * velocity_pressure | Local density + speed variance |
| **EMA** | Trend prediction for density and risk | alpha=0.3 smoothing factor |
| **Gaussian Heatmap** | Spatial density visualization | sigma=15 |

---

## Risk Scoring

The risk score (0-100%) is computed as:

```
base_score = (density_weight * 0.4) + (surge_weight * 0.3) + (velocity_weight * 0.3)

ml_boost = (pressure_boost * 0.6) + (coherence_boost * 0.4)

final_score = min(base_score + ml_boost, 1.0) * 100
```

| Factor | Weight | What it measures |
|--------|--------|-----------------|
| Density | 40% | People per square meter |
| Surge Rate | 30% | Sudden change in crowd count |
| Velocity | 30% | Movement stagnation (high density + low speed = danger) |
| Pressure Boost | ML | Local crushing force estimate |
| Coherence Boost | ML | Flow disruption (panic indicator) |

---

## Screenshots

> Upload screenshots to a `/docs/screenshots/` folder and uncomment:

<!--
### Dashboard
![Dashboard](docs/screenshots/dashboard.png)

### Live Camera Analysis
![Camera View](docs/screenshots/camera_view.png)

### Analytics
![Analytics](docs/screenshots/analytics.png)

### Alerts
![Alerts](docs/screenshots/alerts.png)
-->

---

## Project Structure

```
CrowdSafe/
├── app.py                         # Entry point
├── config.py                      # Configuration & thresholds
├── requirements.txt               # Dependencies
├── Dockerfile                     # Container build
├── docker-compose.yml             # Multi-service deployment
├── .env.example                   # Environment template
│
├── backend/
│   ├── __init__.py                # App factory
│   ├── extensions.py              # db, socketio instances
│   ├── api/                       # REST API blueprints
│   │   ├── auth.py                #   Authentication
│   │   ├── cameras.py             #   Camera CRUD + upload + stream
│   │   ├── metrics.py             #   Metrics query + export
│   │   ├── alerts.py              #   Alert management
│   │   ├── recordings.py          #   Recording management
│   │   ├── settings_api.py        #   Settings CRUD
│   │   ├── users.py               #   User management
│   │   ├── system.py              #   Health & stats
│   │   └── pages.py               #   Template rendering
│   ├── models/                    # SQLAlchemy models
│   │   ├── camera.py
│   │   ├── metric.py
│   │   ├── alert.py
│   │   ├── recording.py
│   │   ├── user.py
│   │   ├── setting.py
│   │   └── system_log.py
│   ├── services/                  # Business logic
│   │   ├── ai_engine.py           #   YOLOv11s + BoT-SORT + annotation
│   │   ├── crowd_analyzer.py      #   DBSCAN, flow, pressure, EMA
│   │   ├── risk_calculator.py     #   Multi-factor risk scoring
│   │   ├── video_processor.py     #   Background processing thread
│   │   ├── camera_manager.py      #   Singleton processor registry
│   │   ├── alert_manager.py       #   Alert creation + cooldown
│   │   ├── telegram_service.py    #   Telegram notifications
│   │   ├── export_service.py      #   CSV / DOCX / PDF / MD export
│   │   └── auth_service.py        #   JWT authentication
│   ├── utils/                     # Helpers
│   │   ├── decorators.py          #   @token_required, @role_required
│   │   ├── validators.py          #   Input validation
│   │   ├── helpers.py             #   Utilities
│   │   └── logger.py              #   Structured logging
│   └── websockets/
│       └── events.py              # Real-time Socket.IO events
│
├── frontend/
│   ├── templates/                 # Jinja2 HTML templates
│   │   ├── base.html              #   Layout (sidebar nav)
│   │   ├── dashboard.html
│   │   ├── cameras.html
│   │   ├── camera_view.html
│   │   ├── analytics.html
│   │   ├── alerts.html
│   │   ├── settings.html
│   │   ├── user_management.html
│   │   └── login.html
│   └── static/
│       ├── css/main.css           # Dark theme styles
│       ├── img/logo.svg
│       └── js/                    # Page-specific JavaScript
│           ├── main.js            #   Common (auth, WebSocket, IST)
│           ├── dashboard.js
│           ├── cameras.js
│           ├── camera_view.js
│           ├── analytics.js
│           ├── alerts.js
│           ├── settings.js
│           └── users.js
│
├── uploads/                       # Uploaded video files
├── recordings/                    # Analyzed video recordings
├── models/                        # YOLO model weights (.pt)
├── instance/                      # SQLite database
└── logs/                          # Application logs
```

---

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/your-feature`)
3. Commit your changes (`git commit -m "Add your feature"`)
4. Push to the branch (`git push origin feature/your-feature`)
5. Open a Pull Request

---

## License

This project is for educational and research purposes.

---

<p align="center">
  Built with <b>YOLOv11</b> + <b>Flask</b> + <b>BoT-SORT</b>
</p>
