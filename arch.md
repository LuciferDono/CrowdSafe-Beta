# COMPREHENSIVE PROJECT SPECIFICATION
# CrowdSafe - Intelligent Crowd Density Monitoring & Stampede Prevention Platform
# Professional-Grade Implementation Guide

---

## PROJECT OVERVIEW

You are tasked with building CrowdSafe, a production-ready AI-powered web-based platform for real-time crowd density monitoring, analysis, and stampede prevention. This system will be used by security personnel, event managers, and authorities to monitor crowds at venues, detect dangerous situations, and prevent casualties.

**Target Users:**
- Security teams at large venues (stadiums, concerts, religious gatherings)
- Event organizers and managers
- City surveillance authorities
- Emergency response teams

**Core Purpose:**
- Monitor crowd density in real-time
- Detect potential stampede conditions before they occur
- Alert authorities immediately when risk levels escalate
- Provide actionable insights for crowd management
- Maintain historical analytics for planning

---

## TECHNICAL REQUIREMENTS

### PRIMARY TECHNOLOGY STACK

**AI/ML Layer:**
- YOLOv11 (latest version) for person detection and tracking
- Built-in BoT-SORT tracker (from Ultralytics)
- Custom density estimation algorithm (grid-based)
- PyTorch as the deep learning framework
- OpenCV for computer vision operations

**Backend:**
- Python 3.11+
- Flask 3.0+ as the web framework
- Flask-SocketIO for real-time bidirectional communication
- SQLAlchemy 2.0+ as ORM
- APScheduler for background tasks
- FFmpeg for video processing
- Pillow for image manipulation

**Database:**
- PostgreSQL 15+ for relational data (camera configs, users, alerts)
- TimescaleDB extension for time-series metrics
- Redis 7.x for caching and session management

**Frontend:**
- HTML5, CSS3, JavaScript (ES6+)
- Bootstrap 5.3 for responsive UI
- Socket.io-client for WebSocket connection
- Chart.js 4.x for data visualization
- HLS.js or Video.js for video streaming
- Leaflet.js for floor plan overlays (optional)

**Infrastructure:**
- Docker for containerization
- Docker Compose for multi-container orchestration
- Nginx as reverse proxy and load balancer
- Gunicorn as WSGI server
- SSL/TLS support (Let's Encrypt)

**Third-Party Services:**
- Twilio for SMS alerts (optional)
- SendGrid or SMTP for email notifications
- Push notification service (optional)

---

## DETAILED FEATURE REQUIREMENTS

### 1. CAMERA MANAGEMENT SYSTEM

**Requirements:**

**1.1 Camera Registration & Configuration**
- Add cameras with following inputs:
  - Camera name/identifier
  - Source (RTSP URL, HTTP stream, file path, webcam ID)
  - Physical location description
  - Monitored area in square meters
  - Expected capacity (people)
  - Camera position (latitude, longitude - optional)
  - Camera angle and field of view

**1.2 Camera Connection Manager**
- Support multiple protocols:
  - RTSP streams (rtsp://username:password@ip:port/stream)
  - HTTP/MJPEG streams (http://ip:port/video.mjpg)
  - Local video files (MP4, AVI, MOV)
  - USB/Webcam devices (device ID)
  - RTMP streams
- Automatic reconnection on connection loss
- Connection health monitoring (ping/keep-alive)
- Frame rate adjustment (target FPS setting)
- Resolution management and downscaling
- Buffer management for low-latency streaming

**1.3 Camera Calibration**
- Three calibration methods:
  a) **ArUco Marker Detection** (automatic):
     - Detect ArUco markers in frame
     - Calculate real-world dimensions
     - Auto-compute monitored area
  
  b) **Reference Point Method** (semi-automatic):
     - User marks two points with known distance
     - System calculates pixel-to-meter ratio
     - Computes total area
  
  c) **Manual Input**:
     - User directly inputs area in square meters
     - User specifies capacity

- Perspective correction support
- Region of Interest (ROI) selection
- Multi-zone monitoring (divide area into zones)

**1.4 Camera Management Features**
- List all registered cameras with status
- Edit camera configuration
- Delete/deactivate cameras
- Test camera connection
- View camera metadata
- Clone camera settings
- Bulk operations (activate/deactivate multiple)

---

### 2. AI ENGINE - CROWD DETECTION & ANALYSIS

**Requirements:**

**2.1 Person Detection Module**
- Use YOLOv11 (latest model: yolo11n.pt for speed, yolo11m.pt for accuracy)
- Detect only "person" class (class_id = 0)
- Configurable confidence threshold (default: 0.5)
- Configurable IoU threshold (default: 0.7)
- Non-maximum suppression (NMS) for overlapping detections
- Support for GPU acceleration (CUDA)
- Fallback to CPU if GPU unavailable

**2.2 Crowd Tracking System**
- Implement BoT-SORT tracking (built into Ultralytics)
- Configuration:
  - tracker='botsort.yaml'
  - persist=True for continuous tracking
  - max_age=30 frames
  - min_hits=3
- Track unique individuals across frames
- Maintain track history for velocity calculation
- Handle occlusions gracefully
- Re-identify lost tracks

**2.3 Density Estimation**
- **For Sparse Crowds (< 50 people):**
  - Direct counting from YOLOv11 detections
  - Calculate: density = count / area_sqm
  
- **For Dense Crowds (≥ 50 people):**
  - Grid-based estimation algorithm:
    - Divide frame into 50x50 pixel grids
    - Count detections per grid
    - Estimate occluded people using density patterns
    - Apply occlusion factor (1.3x multiplier)
    - Smooth density map using Gaussian blur
  
- **Density Heatmap Generation:**
  - Create 2D density distribution map
  - Color coding: Blue (low) → Yellow → Red (high)
  - Overlay on video feed
  - Export as PNG for reports

**2.4 Crowd Behavior Analysis**

**Velocity Calculation:**
- Track center point of each person
- Calculate displacement between frames
- Convert pixel movement to meters/second
- Formula: velocity = (distance_pixels * pixel_to_meter_ratio * fps) / frames
- Compute average velocity for entire crowd
- Detect stagnation (velocity < 0.2 m/s)

**Flow Rate Analysis:**
- Count people entering monitored area
- Count people exiting monitored area
- Calculate net flow rate (people per minute)
- Detect bottlenecks (high inflow, low outflow)

**Surge Detection:**
- Track density change over time
- Calculate surge rate: Δdensity / Δtime
- Detect rapid increases (surge > 0.5 people/m²/s)
- Predict potential stampede conditions

**Crowd Direction Analysis:**
- Calculate predominant movement direction
- Detect counter-flows (opposing directions)
- Identify chaotic movement patterns
- Visualize flow vectors on UI

---

### 3. RISK ASSESSMENT ENGINE

**Requirements:**

**3.1 Multi-Factor Risk Calculation**

Risk is computed using weighted formula:
```
Risk_Score = (w1 × Density_normalized) + 
             (w2 × Surge_normalized) + 
             (w3 × Velocity_inverse_normalized)
```

**Default Weights:**
- w1 (Density weight) = 0.4
- w2 (Surge weight) = 0.3
- w3 (Velocity weight) = 0.3

**Normalization:**
- Density: Normalize to 0-1 scale (max reference: 10 people/m²)
- Surge: Normalize to 0-1 scale (max reference: 2 people/m²/s)
- Velocity: Inverse normalize (lower velocity = higher risk)

**3.2 Risk Level Classification**

**Risk Levels:**

1. **SAFE (Green)** - Risk Score: 0-25
   - Density: 0-2 people/m²
   - Movement: Normal (> 1.0 m/s)
   - Conditions: Well-dispersed crowd
   - Action: Normal monitoring

2. **CAUTION (Yellow)** - Risk Score: 25-50
   - Density: 2-4 people/m²
   - Movement: Slowing (0.5-1.0 m/s)
   - Conditions: Crowd building up
   - Action: Increased monitoring, prepare personnel

3. **WARNING (Orange)** - Risk Score: 50-75
   - Density: 4-6 people/m²
   - Movement: Restricted (0.2-0.5 m/s)
   - Conditions: High density, limited movement
   - Action: Alert security, consider entry restrictions

4. **CRITICAL (Red)** - Risk Score: 75-100
   - Density: > 6 people/m²
   - Movement: Stagnant (< 0.2 m/s)
   - Conditions: Extremely high density, minimal movement
   - Action: IMMEDIATE evacuation, emergency protocols

**3.3 Threshold Configuration**
- Admin can adjust risk thresholds
- Per-camera threshold overrides
- Time-based threshold changes (peak hours)
- Event-specific profiles (concert vs. religious gathering)

**3.4 Predictive Analysis**
- Trend analysis using last 60 seconds of data
- Predict density in next 2-5 minutes
- Early warning system (alert 30s before reaching critical)
- Machine learning for pattern recognition (future enhancement)

---

### 4. REAL-TIME ALERT & NOTIFICATION SYSTEM

**Requirements:**

**4.1 Alert Trigger Conditions**

Alerts triggered when:
- Risk level reaches WARNING or CRITICAL
- Sudden surge detected (>0.8 people/m²/s)
- Velocity drops below 0.2 m/s with density >4
- Capacity exceeded by 10%
- Camera connection lost
- System error/malfunction

**4.2 Multi-Channel Alert Delivery**

**In-Dashboard Alerts:**
- Real-time notification banners
- Visual indicators (flashing borders)
- Color-coded camera tiles
- Sound alerts (configurable)
- Alert history panel
- Acknowledge/dismiss functionality

**Email Notifications:**
- Configurable recipients list
- HTML-formatted emails with metrics
- Attached snapshot of current frame
- Link to live dashboard
- Severity-based subject lines
- Send via SMTP or SendGrid API

**SMS Alerts (Optional):**
- Via Twilio API
- Send to emergency contacts
- Character-limited critical info
- Include camera location
- Configurable for WARNING and CRITICAL only

**Audio Alarms:**
- Browser-based alarm sound
- Different tones for different levels
- Volume control
- Snooze functionality (5-15 minutes)
- Auto-repeat for critical alerts

**Push Notifications (Optional):**
- For mobile app users
- High-priority notifications
- Rich notifications with images
- Action buttons (View, Acknowledge)

**4.3 Alert Cooldown & Deduplication**
- Prevent alert spam
- Cooldown period: 60 seconds (configurable)
- Only send new alert if risk level escalates
- Track alert history to avoid duplicates
- "All clear" notification when risk drops

**4.4 Escalation Protocol**
- Level 1 (CAUTION): Dashboard only
- Level 2 (WARNING): Dashboard + Email to security
- Level 3 (CRITICAL): All channels + SMS to managers
- Level 4 (Emergency): Integrate with emergency services API

---

### 5. WEB DASHBOARD - USER INTERFACE

**Requirements:**

**5.1 Main Dashboard Layout**

**Header Section:**
- Application logo and title
- Real-time clock
- Global alert indicator (shows highest risk across all cameras)
- User profile dropdown (name, role, logout)
- Settings icon

**Camera Grid View:**
- Display all active cameras in grid layout (2x2, 3x3, 4x4 - user selectable)
- Each camera tile shows:
  - Live video feed with annotations
  - Camera name and location
  - Current crowd count
  - Density value with color indicator
  - Risk level badge
  - Camera status (online/offline)
- Click tile to expand to full view
- Drag and drop to reorder tiles

**Metrics Panel (Right Sidebar):**
- Current metrics for selected camera:
  - People count (large display)
  - Density (people/m²)
  - Average velocity (m/s)
  - Surge rate
  - Flow rate (in/out)
  - Risk score and level
  - Capacity utilization (%)
- Historical trend mini-charts (last 10 minutes)
- Quick statistics (peak count, average density)

**Alert Panel (Bottom):**
- Scrolling alert feed
- Timestamp, camera, risk level, message
- Filter by severity
- Acknowledge button
- Auto-scroll to latest
- Alert counter badge

**5.2 Single Camera View**

**Full-Screen Video Feed:**
- Large video player with live annotated stream
- Bounding boxes around detected people
- Track IDs displayed
- Density heatmap overlay (toggle on/off)
- Direction vectors (toggle on/off)
- Zone boundaries (if configured)
- Timestamp overlay

**Live Metrics Overlay:**
- Translucent panel on video
- Real-time updating metrics
- Risk level indicator with color
- Alert status

**Controls Bar:**
- Play/Pause live feed
- Take snapshot
- Record clip (30s/1min/5min)
- Toggle annotations
- Toggle heatmap
- Zoom controls
- Full-screen mode

**5.3 Analytics Dashboard**

**Time-Series Charts:**
- Density trend chart (last 1hr, 6hr, 24hr, 7days)
- Crowd count over time
- Velocity trend
- Risk score timeline
- Comparative analysis (multiple cameras)

**Heatmaps:**
- Spatial density distribution
- High-risk zone identification
- Time-based heatmap (show busy hours)

**Statistics Cards:**
- Total alerts today
- Average crowd count
- Peak density reached
- Average risk score
- Alert response time
- System uptime

**Reports:**
- Daily summary report
- Weekly analytics
- Incident reports
- Custom date range reports
- Export as PDF/Excel

**5.4 Camera Management Interface**

**Camera List Table:**
- Sortable columns (name, status, location, count)
- Search/filter functionality
- Bulk actions (activate, deactivate, delete)
- Status indicators (green/red dots)

**Add Camera Form:**
- Multi-step wizard
- Step 1: Basic info (name, location)
- Step 2: Connection details (protocol, URL)
- Step 3: Calibration (area, capacity)
- Step 4: Test connection
- Step 5: Confirm and save

**Edit Camera Modal:**
- Update all camera settings
- Test connection button
- Recalibrate option
- View camera logs

**5.5 Settings Panel**

**General Settings:**
- Application name customization
- Time zone selection
- Language (English default, expandable)
- Theme (light/dark mode)

**Alert Settings:**
- Enable/disable alert channels
- Configure email recipients
- Set SMS recipients
- Audio volume control
- Cooldown period adjustment

**Risk Thresholds:**
- Adjust density thresholds
- Modify velocity limits
- Change risk weights (w1, w2, w3)
- Set capacity warning percentages

**User Management (Admin only):**
- Add/edit/delete users
- Assign roles (Admin, Operator, Viewer)
- Set permissions
- View user activity logs

**System Settings:**
- GPU/CPU selection
- Target FPS configuration
- Video resolution settings
- Storage retention policy
- Backup settings

**5.6 Mobile Responsive Design**
- Fully responsive layout
- Touch-friendly controls
- Swipe gestures for camera switching
- Simplified mobile dashboard
- Priority information display

---

### 6. VIDEO STREAMING & PROCESSING

**Requirements:**

**6.1 Video Ingestion Pipeline**
- Multi-threaded frame capture
- Frame buffer management (queue size: 30 frames)
- Drop old frames if processing lags
- Frame preprocessing:
  - Resize to target resolution (640x480, 1280x720, or original)
  - Color space conversion (BGR to RGB)
  - Normalization for AI models
  - ROI extraction if configured

**6.2 AI Processing Pipeline**
- Async processing to avoid blocking
- Process every Nth frame (configurable skip rate)
- Batch processing for multiple cameras
- GPU queue management
- Result caching (5 second TTL)

**6.3 Video Streaming to Frontend**

**Method 1: MJPEG Streaming (Simple)**
- Generate JPEG frames
- Stream via multipart/x-mixed-replace
- Low latency (200-500ms)
- Higher bandwidth usage

**Method 2: HLS Streaming (Scalable)**
- Convert stream to HLS format using FFmpeg
- Generate .m3u8 playlist and .ts segments
- Lower bandwidth, higher latency (2-5s)
- Better for multiple viewers

**Method 3: WebRTC (Ultra Low Latency - Advanced)**
- Peer-to-peer connection
- Sub-second latency (<500ms)
- More complex implementation
- Best for critical monitoring

**Recommendation: Start with MJPEG, add HLS for scalability**

**6.4 Frame Annotation**
- Draw bounding boxes (color-coded by risk)
- Display track IDs
- Show confidence scores
- Overlay density heatmap
- Add direction arrows
- Render text info (count, density)
- Export annotated frames

**6.5 Recording & Snapshots**
- Record video clips on-demand
- Auto-record on critical alerts
- Save as MP4 with H.264 codec
- Generate thumbnails
- Store metadata (timestamp, metrics)
- Retention policy (30 days default)

---

### 7. DATABASE SCHEMA

**Requirements:**

**7.1 Tables Structure**

**users** (Authentication & Authorization)
```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(100),
    role VARCHAR(20) DEFAULT 'viewer',  -- admin, operator, viewer
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP,
    phone VARCHAR(20),
    notification_preferences JSONB
);
```

**cameras** (Camera Configuration)
```sql
CREATE TABLE cameras (
    id SERIAL PRIMARY KEY,
    camera_id VARCHAR(50) UNIQUE NOT NULL,  -- e.g., CAM001
    name VARCHAR(100) NOT NULL,
    location VARCHAR(200),
    source_type VARCHAR(20),  -- rtsp, http, file, usb
    source_url TEXT,
    area_sqm FLOAT,
    expected_capacity INTEGER,
    calibration_method VARCHAR(20),  -- aruco, manual, reference
    calibration_data JSONB,
    roi JSONB,  -- Region of Interest coordinates
    is_active BOOLEAN DEFAULT TRUE,
    status VARCHAR(20) DEFAULT 'offline',  -- online, offline, error
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    latitude FLOAT,
    longitude FLOAT,
    fps_target INTEGER DEFAULT 30,
    resolution VARCHAR(20) DEFAULT '1280x720',
    metadata JSONB
);
```

**metrics** (Time-Series Data - use TimescaleDB hypertable)
```sql
CREATE TABLE metrics (
    time TIMESTAMPTZ NOT NULL,
    camera_id VARCHAR(50) NOT NULL,
    count INTEGER,
    density FLOAT,
    avg_velocity FLOAT,
    surge_rate FLOAT,
    flow_in INTEGER,
    flow_out INTEGER,
    risk_score FLOAT,
    risk_level VARCHAR(20),
    capacity_utilization FLOAT,
    metadata JSONB
);

-- Convert to hypertable (TimescaleDB)
SELECT create_hypertable('metrics', 'time');

-- Create indexes
CREATE INDEX idx_metrics_camera_time ON metrics (camera_id, time DESC);
CREATE INDEX idx_metrics_risk_level ON metrics (risk_level);
```

**alerts** (Alert History)
```sql
CREATE TABLE alerts (
    id SERIAL PRIMARY KEY,
    alert_id VARCHAR(50) UNIQUE,
    timestamp TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    camera_id VARCHAR(50) REFERENCES cameras(camera_id),
    risk_level VARCHAR(20),
    trigger_condition VARCHAR(100),
    message TEXT,
    metrics_snapshot JSONB,
    acknowledged BOOLEAN DEFAULT FALSE,
    acknowledged_by INTEGER REFERENCES users(id),
    acknowledged_at TIMESTAMPTZ,
    resolved BOOLEAN DEFAULT FALSE,
    resolved_at TIMESTAMPTZ,
    channels_notified JSONB,  -- {email: true, sms: false, ...}
    snapshot_path VARCHAR(255)
);

CREATE INDEX idx_alerts_camera_time ON alerts (camera_id, timestamp DESC);
CREATE INDEX idx_alerts_risk_level ON alerts (risk_level);
CREATE INDEX idx_alerts_unresolved ON alerts (resolved) WHERE resolved = FALSE;
```

**alert_recipients** (Notification Configuration)
```sql
CREATE TABLE alert_recipients (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    camera_id VARCHAR(50) REFERENCES cameras(camera_id),  -- NULL for all cameras
    risk_levels TEXT[],  -- {warning, critical}
    notification_channels JSONB,  -- {email: true, sms: true, push: false}
    is_active BOOLEAN DEFAULT TRUE
);
```

**recordings** (Video Recordings)
```sql
CREATE TABLE recordings (
    id SERIAL PRIMARY KEY,
    recording_id VARCHAR(50) UNIQUE,
    camera_id VARCHAR(50) REFERENCES cameras(camera_id),
    start_time TIMESTAMPTZ,
    end_time TIMESTAMPTZ,
    duration INTEGER,  -- seconds
    file_path VARCHAR(255),
    file_size BIGINT,  -- bytes
    thumbnail_path VARCHAR(255),
    trigger_type VARCHAR(50),  -- manual, alert, scheduled
    metadata JSONB
);
```

**system_logs** (Application Logs)
```sql
CREATE TABLE system_logs (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    level VARCHAR(20),  -- info, warning, error, critical
    component VARCHAR(50),  -- ai_engine, camera_manager, alert_system
    message TEXT,
    details JSONB,
    user_id INTEGER REFERENCES users(id)
);

CREATE INDEX idx_logs_timestamp ON system_logs (timestamp DESC);
CREATE INDEX idx_logs_level ON system_logs (level);
```

**settings** (System Configuration)
```sql
CREATE TABLE settings (
    id SERIAL PRIMARY KEY,
    key VARCHAR(100) UNIQUE NOT NULL,
    value TEXT,
    category VARCHAR(50),
    description TEXT,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_by INTEGER REFERENCES users(id)
);
```

**7.2 Database Operations**
- Use SQLAlchemy ORM for all database operations
- Implement connection pooling (pool size: 20)
- Use prepared statements for security
- Implement database migrations with Alembic
- Schedule automatic backups (daily)
- Implement data retention policy:
  - Metrics: Keep detailed for 30 days, aggregate for 1 year
  - Alerts: Keep for 1 year
  - Recordings: Keep for 30 days (configurable)
  - Logs: Keep for 90 days

---

### 8. API ENDPOINTS

**Requirements:**

**8.1 Authentication Endpoints**

```
POST /api/auth/login
Request: {username, password}
Response: {token, user_info, expires_at}

POST /api/auth/logout
Headers: Authorization: Bearer <token>
Response: {message}

POST /api/auth/refresh
Headers: Authorization: Bearer <token>
Response: {new_token, expires_at}

GET /api/auth/me
Headers: Authorization: Bearer <token>
Response: {user_info}
```

**8.2 Camera Management Endpoints**

```
GET /api/cameras
Response: [{camera_id, name, status, metrics, ...}]

POST /api/cameras
Request: {name, source_type, source_url, area_sqm, ...}
Response: {camera_id, status, message}

GET /api/cameras/{camera_id}
Response: {camera_details, current_metrics, status}

PUT /api/cameras/{camera_id}
Request: {updated_fields}
Response: {camera_id, status, message}

DELETE /api/cameras/{camera_id}
Response: {message}

POST /api/cameras/{camera_id}/test
Response: {connection_status, test_results}

POST /api/cameras/{camera_id}/calibrate
Request: {calibration_method, calibration_data}
Response: {area_sqm, calibration_info}

POST /api/cameras/{camera_id}/start
Response: {status, message}

POST /api/cameras/{camera_id}/stop
Response: {status, message}
```

**8.3 Metrics & Analytics Endpoints**

```
GET /api/metrics/{camera_id}
Query Params: ?start_time=...&end_time=...&interval=1m
Response: {timestamps[], counts[], densities[], risk_scores[]}

GET /api/metrics/{camera_id}/current
Response: {count, density, velocity, risk_level, ...}

GET /api/metrics/{camera_id}/summary
Query Params: ?period=today|week|month
Response: {avg_density, peak_count, total_alerts, ...}

GET /api/analytics/compare
Query Params: ?camera_ids=CAM001,CAM002&metric=density&period=24h
Response: {camera_ids[], data_series[]}

GET /api/analytics/heatmap/{camera_id}
Query Params: ?timestamp=...
Response: {heatmap_image_base64}
```

**8.4 Alert Endpoints**

```
GET /api/alerts
Query Params: ?camera_id=...&risk_level=...&resolved=false&limit=50
Response: [{alert_id, timestamp, camera_id, risk_level, message, ...}]

GET /api/alerts/{alert_id}
Response: {alert_details, metrics_snapshot, snapshot_url}

POST /api/alerts/{alert_id}/acknowledge
Request: {user_id, notes}
Response: {status, message}

POST /api/alerts/{alert_id}/resolve
Request: {resolution_notes}
Response: {status, message}

GET /api/alerts/statistics
Query Params: ?period=today|week|month
Response: {total_alerts, by_level, by_camera, avg_response_time}
```

**8.5 Recording Endpoints**

```
GET /api/recordings
Query Params: ?camera_id=...&start_date=...&end_date=...
Response: [{recording_id, camera_id, start_time, duration, ...}]

POST /api/recordings/{camera_id}/start
Request: {duration_seconds}
Response: {recording_id, status}

POST /api/recordings/{recording_id}/stop
Response: {status, file_info}

GET /api/recordings/{recording_id}/download
Response: Video file stream

DELETE /api/recordings/{recording_id}
Response: {status, message}
```

**8.6 Settings Endpoints**

```
GET /api/settings
Response: {categories: {category_name: {key: value}}}

GET /api/settings/{category}
Response: {key: value, ...}

PUT /api/settings/{category}/{key}
Request: {value}
Response: {status, message}

POST /api/settings/risk-thresholds
Request: {density_warning, density_critical, ...}
Response: {status, updated_thresholds}
```

**8.7 User Management Endpoints (Admin Only)**

```
GET /api/users
Response: [{user_id, username, role, ...}]

POST /api/users
Request: {username, email, password, role, ...}
Response: {user_id, status}

PUT /api/users/{user_id}
Request: {updated_fields}
Response: {status, message}

DELETE /api/users/{user_id}
Response: {status, message}

POST /api/users/{user_id}/reset-password
Response: {temporary_password}
```

**8.8 System Endpoints**

```
GET /api/system/health
Response: {status, uptime, cpu_usage, memory_usage, gpu_usage}

GET /api/system/logs
Query Params: ?level=error&component=ai_engine&limit=100
Response: [{timestamp, level, message, ...}]

GET /api/system/stats
Response: {active_cameras, total_people_detected, total_alerts, ...}
```

---

### 9. WEBSOCKET EVENTS

**Requirements:**

**9.1 Client → Server Events**

```javascript
// Connect
socket.connect()

// Subscribe to camera
socket.emit('subscribe_camera', {camera_id: 'CAM001'})

// Unsubscribe from camera
socket.emit('unsubscribe_camera', {camera_id: 'CAM001'})

// Request current metrics
socket.emit('get_metrics', {camera_id: 'CAM001'})

// Acknowledge alert
socket.emit('acknowledge_alert', {alert_id: 'ALT123', user_id: 1})
```

**9.2 Server → Client Events**

```javascript
// Metrics update (sent every 1 second for subscribed cameras)
socket.on('metrics_update', (data) => {
    // data: {camera_id, count, density, velocity, risk_level, timestamp}
})

// Alert triggered
socket.on('alert', (data) => {
    // data: {alert_id, camera_id, risk_level, message, metrics, timestamp}
})

// Camera status change
socket.on('camera_status', (data) => {
    // data: {camera_id, status, message}
})

// System notification
socket.on('system_notification', (data) => {
    // data: {type, message, level}
})

// Recording status
socket.on('recording_status', (data) => {
    // data: {camera_id, recording_id, status, duration}
})
```

---

### 10. SECURITY REQUIREMENTS

**10.1 Authentication & Authorization**
- JWT-based authentication
- Access tokens valid for 24 hours
- Refresh tokens valid for 7 days
- Password hashing using bcrypt (cost factor: 12)
- Role-based access control (RBAC):
  - **Admin**: Full access
  - **Operator**: View + manage cameras + acknowledge alerts
  - **Viewer**: View only
- Session management with Redis
- Automatic logout after 30 minutes of inactivity

**10.2 API Security**
- HTTPS only (enforce SSL/TLS)
- CORS configuration (whitelist allowed origins)
- Rate limiting:
  - API endpoints: 100 requests/minute per IP
  - Login endpoint: 5 attempts/minute per IP
- Input validation and sanitization
- SQL injection prevention (parameterized queries)
- XSS protection (escape all user inputs)
- CSRF protection for state-changing operations

**10.3 Data Security**
- Encrypt sensitive data at rest (camera credentials)
- Secure storage of API keys (environment variables)
- Database connection encryption
- Video stream encryption (for RTSP/RTMP)
- Secure file uploads (validate file types)
- Access logs for audit trail

**10.4 Camera Security**
- Store camera credentials encrypted
- Support for camera authentication (username/password)
- Validate camera sources (prevent SSRF attacks)
- Isolate camera network (if possible)

---

### 11. PERFORMANCE REQUIREMENTS

**11.1 AI Processing Performance**
- Target FPS: 24-30 for YOLOv11n, 15-20 for YOLOv11m
- GPU utilization: 60-80%
- Inference time: <50ms per frame (with GPU)
- Support for batch processing (up to 4 cameras simultaneously on RTX 3060)

**11.2 Video Streaming Performance**
- Latency: <1 second for MJPEG, <3 seconds for HLS
- Support up to 10 concurrent viewers per camera
- Automatic quality adjustment based on network
- Frame drop if client can't keep up

**11.3 Database Performance**
- Write throughput: 1000+ inserts/second (metrics)
- Query response time: <100ms for dashboard queries
- Use database indexing for fast lookups
- Implement query caching (5 second TTL)

**11.4 WebSocket Performance**
- Support 50+ concurrent WebSocket connections
- Message delivery latency: <50ms
- Automatic reconnection on disconnect
- Heartbeat/ping every 30 seconds

**11.5 System Resource Management**
- CPU usage: <70% average
- Memory usage: <8GB for 4 cameras
- GPU memory: <4GB for YOLOv11n
- Disk space: Monitor and alert at 80% full

---

### 12. ERROR HANDLING & LOGGING

**12.1 Error Handling Strategy**
- Try-catch blocks around all critical operations
- Graceful degradation (continue monitoring other cameras if one fails)
- User-friendly error messages
- Technical error details in logs only
- Automatic retry with exponential backoff
- Circuit breaker pattern for external services

**12.2 Logging Requirements**
- Log levels: DEBUG, INFO, WARNING, ERROR, CRITICAL
- Structured logging (JSON format)
- Log rotation (max 100MB per file, keep 10 files)
- Separate log files for:
  - Application logs (app.log)
  - Error logs (error.log)
  - Access logs (access.log)
  - AI processing logs (ai_engine.log)
  - Camera logs (camera_manager.log)

**12.3 Error Scenarios to Handle**
- Camera connection lost
- Model loading failure
- Database connection timeout
- GPU out of memory
- Invalid video format
- Network timeout
- Disk space full
- Configuration error

---

### 13. TESTING REQUIREMENTS

**13.1 Unit Tests**
- Test coverage: >80%
- Test all utility functions
- Test database operations
- Test risk calculation logic
- Test alert trigger conditions
- Use pytest framework

**13.2 Integration Tests**
- Test API endpoints
- Test WebSocket communication
- Test camera connection
- Test alert delivery
- Test database transactions

**13.3 Performance Tests**
- Load test with multiple cameras
- Stress test AI processing
- Database query performance
- WebSocket scalability

**13.4 End-to-End Tests**
- Complete user workflows
- Camera addition and monitoring
- Alert flow from detection to notification
- Recording and playback

---

### 14. DEPLOYMENT REQUIREMENTS

**14.1 Docker Configuration**

**Dockerfile for Backend:**
```dockerfile
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libopencv-dev \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port
EXPOSE 5000

# Run application
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "4", "--timeout", "120", "app:app"]
```

**14.2 Docker Compose**
- Define services: backend, postgres, redis, nginx
- Set up networking between containers
- Configure volumes for persistent data
- Environment variable management
- Health checks for all services

**14.3 Environment Variables**
```
# Application
FLASK_ENV=production
SECRET_KEY=<random-secret-key>
DEBUG=False

# Database
DATABASE_URL=postgresql://user:password@postgres:5432/crowdsafe
REDIS_URL=redis://redis:6379/0

# AI
GPU_ENABLED=True
MODEL_PATH=/app/models/yolo11n.pt

# Alerts
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=alerts@crowdsafe.com
SMTP_PASSWORD=<password>
TWILIO_ACCOUNT_SID=<sid>
TWILIO_AUTH_TOKEN=<token>
TWILIO_PHONE_NUMBER=<phone>

# Security
JWT_SECRET_KEY=<jwt-secret>
JWT_ACCESS_TOKEN_EXPIRES=86400  # 24 hours
```

**14.4 Production Checklist**
- Enable HTTPS with SSL certificate
- Configure firewall rules
- Set up log aggregation
- Configure automated backups
- Set up monitoring and alerts
- Document deployment process
- Prepare rollback procedure

---

### 15. DOCUMENTATION REQUIREMENTS

**15.1 Code Documentation**
- Docstrings for all functions and classes
- Inline comments for complex logic
- Type hints for function parameters

**15.2 API Documentation**
- Generate with Swagger/OpenAPI
- Include examples for all endpoints
- Document error responses
- Include authentication requirements

**15.3 User Documentation**
- Installation guide
- User manual with screenshots
- Admin guide
- Troubleshooting guide
- FAQ section

**15.4 Developer Documentation**
- Architecture overview
- Database schema documentation
- Deployment guide
- Contributing guidelines
- Testing guide

---

## PROJECT STRUCTURE

Implement the following directory structure:

```
crowdsafe/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                    # Flask application entry point
│   │   ├── config.py                  # Configuration management
│   │   ├── extensions.py              # Flask extensions (SQLAlchemy, SocketIO, etc.)
│   │   │
│   │   ├── models/                    # Database models
│   │   │   ├── __init__.py
│   │   │   ├── user.py
│   │   │   ├── camera.py
│   │   │   ├── metric.py
│   │   │   ├── alert.py
│   │   │   ├── recording.py
│   │   │   └── setting.py
│   │   │
│   │   ├── api/                       # API routes
│   │   │   ├── __init__.py
│   │   │   ├── auth.py
│   │   │   ├── cameras.py
│   │   │   ├── metrics.py
│   │   │   ├── alerts.py
│   │   │   ├── recordings.py
│   │   │   ├── settings.py
│   │   │   ├── users.py
│   │   │   └── system.py
│   │   │
│   │   ├── services/                  # Business logic
│   │   │   ├── __init__.py
│   │   │   ├── camera_manager.py      # Camera connection & management
│   │   │   ├── ai_engine.py           # YOLOv11 + tracking
│   │   │   ├── risk_calculator.py     # Risk assessment logic
│   │   │   ├── alert_manager.py       # Alert delivery
│   │   │   ├── video_processor.py     # Video streaming & recording
│   │   │   └── auth_service.py        # Authentication
│   │   │
│   │   ├── utils/                     # Helper functions
│   │   │   ├── __init__.py
│   │   │   ├── decorators.py          # Auth decorators
│   │   │   ├── validators.py
│   │   │   ├── logger.py
│   │   │   └── helpers.py
│   │   │
│   │   ├── websockets/                # WebSocket handlers
│   │   │   ├── __init__.py
│   │   │   └── events.py
│   │   │
│   │   └── tasks/                     # Background tasks
│   │       ├── __init__.py
│   │       ├── monitoring.py
│   │       └── cleanup.py
│   │
│   ├── migrations/                    # Alembic migrations
│   ├── tests/                         # Test files
│   │   ├── test_api/
│   │   ├── test_services/
│   │   └── test_models/
│   │
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env.example
│
├── frontend/
│   ├── static/
│   │   ├── css/
│   │   │   ├── main.css
│   │   │   ├── dashboard.css
│   │   │   └── bootstrap.min.css
│   │   │
│   │   ├── js/
│   │   │   ├── main.js
│   │   │   ├── dashboard.js
│   │   │   ├── camera_manager.js
│   │   │   ├── analytics.js
│   │   │   ├── alerts.js
│   │   │   └── websocket.js
│   │   │
│   │   ├── img/
│   │   │   ├── logo.png
│   │   │   └── icons/
│   │   │
│   │   └── sounds/
│   │       ├── alert_warning.mp3
│   │       └── alert_critical.mp3
│   │
│   └── templates/
│       ├── base.html                  # Base template
│       ├── login.html
│       ├── dashboard.html             # Main dashboard
│       ├── camera_view.html           # Single camera view
│       ├── analytics.html
│       ├── camera_management.html
│       ├── settings.html
│       └── user_management.html
│
├── models/                            # AI model weights
│   ├── yolo11n.pt
│   └── botsort.yaml
│
├── docker-compose.yml
├── nginx.conf
├── .gitignore
├── README.md
├── LICENSE
└── docs/
    ├── API.md
    ├── DEPLOYMENT.md
    ├── USER_GUIDE.md
    └── ARCHITECTURE.md
```

---

## DEVELOPMENT PHASES

### Phase 1: Core Infrastructure (Week 1-2)
1. Set up project structure
2. Configure Flask application
3. Set up database with SQLAlchemy
4. Implement authentication system
5. Create basic API endpoints
6. Set up logging and error handling

### Phase 2: AI Engine (Week 3-4)
1. Integrate YOLOv11 model
2. Implement BoT-SORT tracking
3. Develop density estimation algorithm
4. Create risk calculation engine
5. Test with sample videos
6. Optimize performance

### Phase 3: Camera Management (Week 5-6)
1. Implement camera connection manager
2. Support multiple streaming protocols
3. Develop calibration methods
4. Create camera CRUD API
5. Implement video streaming
6. Add recording functionality

### Phase 4: Frontend Dashboard (Week 7-8)
1. Design responsive UI
2. Implement dashboard layout
3. Add live video feeds
4. Create metrics visualizations
5. Build analytics charts
6. Implement camera management UI

### Phase 5: Real-time Features (Week 9-10)
1. Implement WebSocket communication
2. Real-time metrics updates
3. Live alert notifications
4. Audio alert system
5. Test with multiple cameras
6. Optimize WebSocket performance

### Phase 6: Alert System (Week 11)
1. Implement alert trigger logic
2. Add email notifications
3. Integrate SMS (Twilio)
4. Create alert management UI
5. Test alert delivery
6. Implement escalation protocol

### Phase 7: Analytics & Reporting (Week 12)
1. Create time-series queries
2. Build analytics dashboard
3. Generate reports
4. Export functionality
5. Historical data analysis
6. Predictive analytics

### Phase 8: Testing & Optimization (Week 13-14)
1. Write unit tests
2. Perform integration testing
3. Load testing
4. Security testing
5. Performance optimization
6. Bug fixes

### Phase 9: Deployment (Week 15-16)
1. Create Docker containers
2. Set up docker-compose
3. Configure Nginx
4. SSL/TLS setup
5. Production deployment
6. Monitoring setup
7. Documentation finalization

---

## SAMPLE CODE SNIPPETS

### AI Engine Implementation:

```python
# backend/app/services/ai_engine.py

import torch
from ultralytics import YOLO
import cv2
import numpy as np
from typing import Dict, List, Tuple, Optional
import time

class CrowdSafeAI:
    """
    Main AI engine for crowd detection, tracking, and analysis
    """
    
    def __init__(self, model_path: str = 'models/yolo11n.pt', device: str = None):
        """
        Initialize AI engine with YOLOv11 model
        
        Args:
            model_path: Path to YOLOv11 weights
            device: 'cuda' or 'cpu', auto-detect if None
        """
        # Auto-detect device
        if device is None:
            self.device = 'cuda' if torch.cuda.is_available() else 'cpu'
        else:
            self.device = device
        
        print(f"Loading YOLOv11 model on {self.device}...")
        
        # Load YOLOv11 model
        self.model = YOLO(model_path)
        self.model.to(self.device)
        
        # Tracking history for velocity calculation
        self.track_history: Dict[int, List[Tuple[float, float, float]]] = {}
        
        # Configuration
        self.conf_threshold = 0.5
        self.iou_threshold = 0.7
        self.dense_crowd_threshold = 50
        self.grid_size = 50
        
        print("AI Engine initialized successfully")
    
    def analyze_frame(self, frame: np.ndarray, area_sqm: float, 
                     fps: int = 30) -> Dict:
        """
        Main analysis function
        
        Args:
            frame: Input frame (BGR format)
            area_sqm: Monitored area in square meters
            fps: Frame rate for velocity calculation
            
        Returns:
            Dictionary with analysis results
        """
        start_time = time.time()
        
        # Run YOLOv11 detection with tracking
        results = self.model.track(
            frame,
            persist=True,
            tracker='botsort.yaml',
            classes=[0],  # Person class only
            conf=self.conf_threshold,
            iou=self.iou_threshold,
            verbose=False
        )
        
        # Extract detection data
        if results[0].boxes.id is not None:
            boxes = results[0].boxes.xyxy.cpu().numpy()
            track_ids = results[0].boxes.id.int().cpu().numpy()
            confidences = results[0].boxes.conf.cpu().numpy()
            
            count = len(track_ids)
            
            # Determine detection method
            if count < self.dense_crowd_threshold:
                # Direct counting for sparse crowds
                density = count / area_sqm
                method = 'direct_detection'
                density_map = self._create_simple_density_map(frame, boxes)
            else:
                # Grid-based estimation for dense crowds
                estimated_count = self._estimate_dense_crowd(frame, boxes)
                density = estimated_count / area_sqm
                count = estimated_count
                method = 'grid_estimation'
                density_map = self._create_density_map(frame, boxes)
            
            # Calculate velocities and flow
            velocities = self._calculate_velocities(track_ids, boxes, fps)
            avg_velocity = np.mean(velocities) if len(velocities) > 0 else 0.0
            
            flow_data = self._analyze_flow(track_ids, boxes)
            
            # Create annotated frame
            annotated_frame = self._draw_annotations(
                frame, boxes, track_ids, confidences, density, avg_velocity
            )
            
            processing_time = time.time() - start_time
            
            return {
                'success': True,
                'count': int(count),
                'density': round(density, 2),
                'avg_velocity': round(avg_velocity, 2),
                'flow_in': flow_data['flow_in'],
                'flow_out': flow_data['flow_out'],
                'boxes': boxes.tolist(),
                'track_ids': track_ids.tolist(),
                'confidences': confidences.tolist(),
                'density_map': density_map,
                'annotated_frame': annotated_frame,
                'method': method,
                'processing_time_ms': round(processing_time * 1000, 2),
                'timestamp': time.time()
            }
        else:
            # No detections
            return {
                'success': True,
                'count': 0,
                'density': 0.0,
                'avg_velocity': 0.0,
                'flow_in': 0,
                'flow_out': 0,
                'boxes': [],
                'track_ids': [],
                'confidences': [],
                'density_map': np.zeros((frame.shape[0], frame.shape[1])),
                'annotated_frame': frame,
                'method': 'no_detection',
                'processing_time_ms': round((time.time() - start_time) * 1000, 2),
                'timestamp': time.time()
            }
    
    def _calculate_velocities(self, track_ids: np.ndarray, 
                             boxes: np.ndarray, fps: int) -> List[float]:
        """Calculate velocity for each tracked person"""
        velocities = []
        current_time = time.time()
        
        for tid, box in zip(track_ids, boxes):
            # Calculate center point
            cx = (box[0] + box[2]) / 2
            cy = (box[1] + box[3]) / 2
            current_pos = (cx, cy, current_time)
            
            # Calculate velocity if we have previous position
            if tid in self.track_history and len(self.track_history[tid]) > 0:
                prev_cx, prev_cy, prev_time = self.track_history[tid][-1]
                
                # Distance in pixels
                distance_pixels = np.sqrt((cx - prev_cx)**2 + (cy - prev_cy)**2)
                
                # Time difference
                time_diff = current_time - prev_time
                
                if time_diff > 0:
                    # Approximate conversion: assuming 100 pixels ≈ 1 meter
                    # This should be calibrated per camera
                    pixel_to_meter = 0.01
                    distance_meters = distance_pixels * pixel_to_meter
                    velocity = distance_meters / time_diff  # m/s
                    velocities.append(velocity)
            
            # Update track history (keep last 30 positions)
            if tid not in self.track_history:
                self.track_history[tid] = []
            
            self.track_history[tid].append(current_pos)
            if len(self.track_history[tid]) > 30:
                self.track_history[tid].pop(0)
        
        # Clean up old tracks
        active_ids = set(track_ids)
        self.track_history = {k: v for k, v in self.track_history.items() 
                            if k in active_ids}
        
        return velocities
    
    def _analyze_flow(self, track_ids: np.ndarray, 
                     boxes: np.ndarray) -> Dict:
        """Analyze crowd flow (in/out)"""
        # Simplified implementation
        # In production, define entry/exit zones
        flow_in = 0
        flow_out = 0
        
        # TODO: Implement proper flow analysis based on ROI zones
        
        return {
            'flow_in': flow_in,
            'flow_out': flow_out
        }
    
    def _estimate_dense_crowd(self, frame: np.ndarray, 
                             boxes: np.ndarray) -> int:
        """Estimate count for dense crowds using grid method"""
        h, w = frame.shape[:2]
        grid_h = h // self.grid_size
        grid_w = w // self.grid_size
        
        # Create grid
        grid = np.zeros((grid_h, grid_w))
        
        # Mark grids with detected people
        for box in boxes:
            x1, y1, x2, y2 = box
            cx, cy = (x1 + x2) / 2, (y1 + y2) / 2
            gx, gy = int(cx / self.grid_size), int(cy / self.grid_size)
            
            if 0 <= gx < grid_w and 0 <= gy < grid_h:
                grid[gy, gx] += 1
        
        # Calculate average density in occupied grids
        occupied_grids = grid > 0
        if occupied_grids.sum() > 0:
            avg_per_grid = grid[occupied_grids].mean()
            total_occupied = occupied_grids.sum()
            
            # Estimate with occlusion factor
            occlusion_factor = 1.3
            estimated_total = int(total_occupied * avg_per_grid * occlusion_factor)
            
            return estimated_total
        
        return len(boxes)
    
    def _create_density_map(self, frame: np.ndarray, 
                           boxes: np.ndarray) -> np.ndarray:
        """Create density heatmap"""
        h, w = frame.shape[:2]
        density_map = np.zeros((h, w), dtype=np.float32)
        
        # Add Gaussian around each detection
        for box in boxes:
            x1, y1, x2, y2 = map(int, box)
            cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
            
            # Create Gaussian kernel
            kernel_size = 50
            sigma = 15
            
            y_min = max(0, cy - kernel_size)
            y_max = min(h, cy + kernel_size)
            x_min = max(0, cx - kernel_size)
            x_max = min(w, cx + kernel_size)
            
            y_coords, x_coords = np.ogrid[y_min:y_max, x_min:x_max]
            gaussian = np.exp(-((x_coords - cx)**2 + (y_coords - cy)**2) / (2 * sigma**2))
            
            density_map[y_min:y_max, x_min:x_max] += gaussian
        
        # Normalize
        if density_map.max() > 0:
            density_map = density_map / density_map.max()
        
        return density_map
    
    def _create_simple_density_map(self, frame: np.ndarray, 
                                   boxes: np.ndarray) -> np.ndarray:
        """Create simple density map for sparse crowds"""
        h, w = frame.shape[:2]
        density_map = np.zeros((h, w), dtype=np.float32)
        
        for box in boxes:
            x1, y1, x2, y2 = map(int, box)
            density_map[y1:y2, x1:x2] = 1.0
        
        return density_map
    
    def _draw_annotations(self, frame: np.ndarray, boxes: np.ndarray,
                         track_ids: np.ndarray, confidences: np.ndarray,
                         density: float, avg_velocity: float) -> np.ndarray:
        """Draw bounding boxes and info on frame"""
        annotated = frame.copy()
        
        # Color map for risk levels
        color_map = {
            'safe': (0, 255, 0),      # Green
            'caution': (0, 255, 255),  # Yellow
            'warning': (0, 165, 255),  # Orange
            'critical': (0, 0, 255)    # Red
        }
        
        # Determine color based on density
        if density < 2.0:
            color = color_map['safe']
            risk_text = 'SAFE'
        elif density < 4.0:
            color = color_map['caution']
            risk_text = 'CAUTION'
        elif density < 6.0:
            color = color_map['warning']
            risk_text = 'WARNING'
        else:
            color = color_map['critical']
            risk_text = 'CRITICAL'
        
        # Draw boxes
        for box, tid, conf in zip(boxes, track_ids, confidences):
            x1, y1, x2, y2 = map(int, box)
            
            cv2.rectangle(annotated, (x1, y1), (x2, y2), color, 2)
            
            label = f'ID:{tid} {conf:.2f}'
            (label_w, label_h), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
            cv2.rectangle(annotated, (x1, y1 - label_h - 10), 
                         (x1 + label_w, y1), color, -1)
            cv2.putText(annotated, label, (x1, y1 - 5),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        # Draw info panel
        panel_height = 150
        panel = np.zeros((panel_height, annotated.shape[1], 3), dtype=np.uint8)
        
        info_text = [
            f"Count: {len(boxes)}",
            f"Density: {density:.2f} p/m²",
            f"Velocity: {avg_velocity:.2f} m/s",
            f"Risk: {risk_text}"
        ]
        
        y_offset = 30
        for text in info_text:
            cv2.putText(panel, text, (20, y_offset),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            y_offset += 35
        
        # Add timestamp
        timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
        cv2.putText(panel, timestamp, (annotated.shape[1] - 200, 30),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)
        
        # Combine panel with frame
        annotated = np.vstack([panel, annotated])
        
        return annotated
    
    def create_heatmap_overlay(self, frame: np.ndarray, 
                               density_map: np.ndarray) -> np.ndarray:
        """Create colored heatmap overlay on frame"""
        # Resize density map to frame size
        density_resized = cv2.resize(density_map, (frame.shape[1], frame.shape[0]))
        
        # Normalize to 0-255
        heatmap_normalized = (density_resized * 255).astype(np.uint8)
        
        # Apply colormap
        heatmap_colored = cv2.applyColorMap(heatmap_normalized, cv2.COLORMAP_JET)
        
        # Blend with original frame
        alpha = 0.4
        blended = cv2.addWeighted(frame, 1 - alpha, heatmap_colored, alpha, 0)
        
        return blended
```

---

## DEVELOPMENT INSTRUCTIONS

**Implementation Order:**
1. Start with database models and basic Flask setup
2. Implement AI engine with sample video testing
3. Build API endpoints incrementally
4. Create frontend templates with static data first
5. Integrate WebSocket for real-time updates
6. Add alert system
7. Implement camera management
8. Build analytics dashboard
9. Add security features
10. Optimize and test

**Testing During Development:**
- Test each component independently before integration
- Use sample videos for AI testing (download from YouTube)
- Create mock data for frontend development
- Use Postman for API testing
- Implement logging at every step for debugging

**Code Quality Standards:**
- Follow PEP 8 for Python code
- Add docstrings to all functions
- Use type hints
- Write descriptive variable names
- Add comments for complex logic
- Handle exceptions properly
- Validate all inputs

**Git Workflow:**
- Create feature branches for major components
- Commit frequently with clear messages
- Use .gitignore for sensitive files and large models
- Tag releases (v1.0, v1.1, etc.)

**Performance Monitoring:**
- Log processing time for each frame
- Monitor GPU usage
- Track database query times
- Measure API response times
- Set up alerts for performance degradation

---

## SUCCESS CRITERIA

The project is considered complete when:

✅ Multiple cameras can be added and monitored simultaneously
✅ AI detection achieves >80% accuracy on test videos
✅ System processes frames at 20+ FPS
✅ Dashboard updates in real-time (<1s latency)
✅ Alerts are delivered within 3 seconds of trigger
✅ System runs stable for 24+ hours without crashes
✅ All API endpoints are functional and documented
✅ Security features are implemented and tested
✅ Database handles 10,000+ metric inserts per minute
✅ Video streaming works with <2s latency
✅ Frontend is responsive and works on mobile
✅ Documentation is complete and clear

---

## ADDITIONAL NOTES

1. **Model Downloads:**
   - YOLOv11: Auto-downloads on first run via Ultralytics
   - BoT-SORT config: Included in Ultralytics package

2. **Sample Data for Testing:**
   - Use YouTube videos of crowds (download with youtube-dl)
   - Test with different scenarios: sparse, dense, moving, static
   - Validate against manual counts

3. **Production Considerations:**
   - Use environment variables for all secrets
   - Implement database backups
   - Set up monitoring (Prometheus + Grafana)
   - Configure log rotation
   - Implement rate limiting
   - Set up SSL certificates

4. **Scalability:**
   - Design for horizontal scaling from the start
   - Use Redis for session management
   - Implement database connection pooling
   - Consider message queue for high load (RabbitMQ/Kafka)

5. **Future Enhancements:**
   - Mobile app (React Native/Flutter)
   - Advanced analytics with ML predictions
   - Integration with building management systems
   - Multi-tenancy support
   - Advanced reporting with PDF generation
   - Integration with emergency services

---

## FINAL CHECKLIST BEFORE DEPLOYMENT

- [ ] All tests passing
- [ ] Security audit completed
- [ ] Performance testing done
- [ ] Documentation complete
- [ ] User training materials ready
- [ ] Backup and recovery tested
- [ ] Monitoring configured
- [ ] SSL certificates installed
- [ ] Environment variables configured
- [ ] Database migrations run
- [ ] Initial admin user created
- [ ] Sample data loaded (optional)
- [ ] Error handling verified
- [ ] Logging configured properly
- [ ] Resource limits set

---

## SUPPORT & MAINTENANCE PLAN

**Daily:**
- Monitor system health
- Check alert delivery
- Review error logs

**Weekly:**
- Database backup verification
- Performance metrics review
- Security log audit

**Monthly:**
- Model performance evaluation
- Update dependencies
- Capacity planning review

**Quarterly:**
- Security audit
- User feedback review
- Feature prioritization

---

This specification is comprehensive and production-ready. Follow it systematically, and you'll have a professional-grade crowd monitoring platform.

Build with quality, test thoroughly, and prioritize user experience.

Good luck! 🚀