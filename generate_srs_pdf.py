"""Generate SRS.pdf from SRS.md content using reportlab."""

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.colors import HexColor, black, white
from reportlab.lib.units import mm, cm
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, KeepTogether
)
from reportlab.lib import colors

W, H = A4

# Colors
DARK_BG = HexColor('#1a1d24')
ACCENT = HexColor('#4f8ff7')
HEADER_BG = HexColor('#2a3040')
ROW_ALT = HexColor('#f5f7fa')
BORDER_CLR = HexColor('#cccccc')
GREEN = HexColor('#28a745')
YELLOW = HexColor('#ffc107')
ORANGE = HexColor('#ff9500')
RED = HexColor('#dc3545')

styles = getSampleStyleSheet()

# Custom styles
styles.add(ParagraphStyle('DocTitle', parent=styles['Title'], fontSize=24, spaceAfter=6,
                          textColor=HexColor('#1a1d24'), fontName='Helvetica-Bold'))
styles.add(ParagraphStyle('DocSubtitle', parent=styles['Normal'], fontSize=12, spaceAfter=20,
                          textColor=HexColor('#555555'), alignment=TA_CENTER))
styles.add(ParagraphStyle('SectionHead', parent=styles['Heading1'], fontSize=16, spaceBefore=18,
                          spaceAfter=8, textColor=ACCENT, fontName='Helvetica-Bold'))
styles.add(ParagraphStyle('SubHead', parent=styles['Heading2'], fontSize=13, spaceBefore=12,
                          spaceAfter=6, textColor=HexColor('#333333'), fontName='Helvetica-Bold'))
styles.add(ParagraphStyle('Body', parent=styles['Normal'], fontSize=9.5, leading=13,
                          spaceBefore=2, spaceAfter=4))
styles.add(ParagraphStyle('BulletCS', parent=styles['Normal'], fontSize=9.5, leading=13,
                          leftIndent=16, bulletIndent=6, spaceBefore=1, spaceAfter=1))
styles.add(ParagraphStyle('CodeCS', parent=styles['Normal'], fontSize=8.5, leading=11,
                          fontName='Courier', leftIndent=12, spaceBefore=4, spaceAfter=4,
                          backColor=HexColor('#f0f0f0')))
styles.add(ParagraphStyle('TableCell', parent=styles['Normal'], fontSize=8, leading=10))
styles.add(ParagraphStyle('TableHeader', parent=styles['Normal'], fontSize=8, leading=10,
                          fontName='Helvetica-Bold', textColor=white))
styles.add(ParagraphStyle('TOCEntry', parent=styles['Normal'], fontSize=10, leading=16,
                          leftIndent=12))


def make_table(headers, rows, col_widths=None):
    """Create a styled table."""
    header_cells = [Paragraph(h, styles['TableHeader']) for h in headers]
    data = [header_cells]
    for row in rows:
        data.append([Paragraph(str(c), styles['TableCell']) for c in row])

    if col_widths is None:
        avail = W - 50 * mm
        col_widths = [avail / len(headers)] * len(headers)

    t = Table(data, colWidths=col_widths, repeatRows=1)
    style_cmds = [
        ('BACKGROUND', (0, 0), (-1, 0), HEADER_BG),
        ('TEXTCOLOR', (0, 0), (-1, 0), white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 8),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
        ('TOPPADDING', (0, 0), (-1, 0), 6),
        ('GRID', (0, 0), (-1, -1), 0.5, BORDER_CLR),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
        ('TOPPADDING', (0, 1), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 3),
    ]
    for i in range(1, len(data)):
        if i % 2 == 0:
            style_cmds.append(('BACKGROUND', (0, i), (-1, i), ROW_ALT))
    t.setStyle(TableStyle(style_cmds))
    return t


def build_pdf():
    doc = SimpleDocTemplate(
        'SRS.pdf', pagesize=A4,
        leftMargin=22*mm, rightMargin=22*mm,
        topMargin=20*mm, bottomMargin=20*mm,
        title='CrowdSafe - Software Requirements Specification',
        author='CrowdSafe Team',
    )

    story = []
    avail = W - 44 * mm

    # ---- TITLE PAGE ----
    story.append(Spacer(1, 60))
    story.append(Paragraph('CrowdSafe', styles['DocTitle']))
    story.append(Paragraph('Software Requirements Specification', styles['DocSubtitle']))
    story.append(Spacer(1, 20))
    story.append(Paragraph('AI-Powered Crowd Density Monitoring &amp; Stampede Prevention Platform', styles['Body']))
    story.append(Spacer(1, 40))

    # TOC
    story.append(Paragraph('Table of Contents', styles['SubHead']))
    toc_items = [
        '1. Problem Definition', '2. Proposed Solution', '3. Scope',
        '4. Functional Requirements', '5. Non-Functional Requirements',
        '6. System Features', '7. System Architecture', '8. Database Models',
        '9. API Endpoints', '10. Real-Time Events', '11. Notification Channels',
        '12. Configuration Reference', '13. Default Data', '14. Summary Statistics',
    ]
    for item in toc_items:
        story.append(Paragraph(item, styles['TOCEntry']))
    story.append(PageBreak())

    # ---- 1. PROBLEM DEFINITION ----
    story.append(Paragraph('1. Problem Definition', styles['SectionHead']))
    story.append(Paragraph(
        'Large crowd gatherings at festivals, metro stations, stadiums, and religious events pose severe '
        'stampede and crush risks. Manual monitoring fails at scale — by the time a human operator notices '
        'dangerous density levels, it is too late to prevent casualties.', styles['Body']))
    story.append(Spacer(1, 4))
    story.append(Paragraph('Notable Incidents', styles['SubHead']))
    story.append(make_table(
        ['Event', 'Est. Density', 'Casualties', 'Year'],
        [
            ['Mecca Hajj crush', '~9 p/m²', '2,400+', '2015'],
            ['Itaewon crowd crush', '~8 p/m²', '159', '2022'],
            ['Hillsborough disaster', '~7+ p/m²', '97', '1989'],
            ['Love Parade stampede', '~8 p/m²', '21', '2010'],
        ],
        [avail*0.35, avail*0.2, avail*0.2, avail*0.15]
    ))
    story.append(Spacer(1, 4))
    story.append(Paragraph(
        'These incidents demonstrate that real-time, automated crowd density monitoring is a critical '
        'unsolved need. Current surveillance systems rely on passive CCTV footage reviewed by human '
        'operators, which is reactive rather than preventive.', styles['Body']))

    # ---- 2. PROPOSED SOLUTION ----
    story.append(Paragraph('2. Proposed Solution', styles['SectionHead']))
    story.append(Paragraph(
        '<b>CrowdSafe</b> is an AI-powered real-time crowd density monitoring and stampede prevention '
        'platform that uses:', styles['Body']))
    bullets = [
        '<b>YOLOv11s</b> computer vision to detect and count people in video feeds',
        '<b>BoT-SORT</b> multi-object tracking to follow individuals across frames',
        '<b>ML algorithms</b> (DBSCAN, z-score, flow coherence, crowd pressure) to analyze crowd behavior',
        '<b>Multi-factor risk scoring</b> to quantify danger levels in real-time',
        '<b>Multi-channel alerting</b> (Telegram, SocketIO, dashboard) to notify operators',
        '<b>Professional CCTV-style annotations</b> for intuitive visual monitoring',
    ]
    for b in bullets:
        story.append(Paragraph(f'• {b}', styles['BulletCS']))
    story.append(Spacer(1, 4))
    story.append(Paragraph(
        'The system transitions crowd safety from reactive to preventive by providing early warnings '
        'at WARNING (50-74%) and CRITICAL (75-100%) risk levels.', styles['Body']))

    # ---- 3. SCOPE ----
    story.append(Paragraph('3. Scope', styles['SectionHead']))
    scope = [
        ['S1', 'Real-time person detection and tracking from video feeds (uploaded or RTSP)'],
        ['S2', 'Crowd density calculation and risk scoring using multi-factor weighted formula'],
        ['S3', 'ML-based crowd behavior analysis (clustering, flow coherence, pressure, anomalies)'],
        ['S4', 'Automated alert generation with cooldown and escalation'],
        ['S5', 'Multi-channel notifications (Telegram with photo, SocketIO real-time, dashboard)'],
        ['S6', 'Live annotated MJPEG video streaming with professional CCTV-style overlays'],
        ['S7', 'Historical data storage, querying, and time-series analytics'],
        ['S8', 'Data export in 4 formats (CSV, DOCX, PDF, Markdown)'],
        ['S9', 'Role-based user management (admin/operator/viewer)'],
        ['S10', 'Configurable thresholds and AI parameters via settings UI'],
        ['S11', 'Recording of analyzed video sessions for playback'],
        ['S12', 'Density heatmap overlay visualization'],
    ]
    story.append(make_table(['#', 'Scope Item'], scope, [avail*0.08, avail*0.92]))
    story.append(Paragraph('<b>Total: 12 scope items</b>', styles['Body']))

    # ---- 4. FUNCTIONAL REQUIREMENTS ----
    story.append(PageBreak())
    story.append(Paragraph('4. Functional Requirements', styles['SectionHead']))
    frs = [
        ['FR1', 'System shall detect and count people in video frames using YOLOv11s object detection'],
        ['FR2', 'System shall track individuals across frames using BoT-SORT with persistent track IDs'],
        ['FR3', 'System shall calculate crowd density as people_count / area_sqm (persons per m²)'],
        ['FR4', 'System shall compute risk score: 40% density + 30% surge + 30% velocity + ML boosts'],
        ['FR5', 'System shall classify risk into 4 levels: SAFE (0-24%), CAUTION (25-49%), WARNING (50-74%), CRITICAL (75-100%)'],
        ['FR6', 'System shall generate alerts at WARNING/CRITICAL with 60-second cooldown per camera'],
        ['FR7', 'System shall send Telegram notifications with annotated frame snapshot on alert'],
        ['FR8', 'System shall stream live annotated video via MJPEG with bounding boxes, HUD, sparkline'],
        ['FR9', 'System shall perform DBSCAN spatial clustering to detect crowd groups'],
        ['FR10', 'System shall detect velocity anomalies using z-score analysis (threshold: 2.0)'],
        ['FR11', 'System shall calculate flow coherence (0-1) as stampede indicator'],
        ['FR12', 'System shall estimate crowd pressure from nearest-neighbor distance + velocity variance'],
        ['FR13', 'System shall predict density/risk trends using exponential moving average'],
        ['FR14', 'System shall support date-range filtering on analytics (1H, 24H, 7D, 30D, All, Custom)'],
        ['FR15', 'System shall export metrics data in CSV, DOCX, PDF, and Markdown formats'],
        ['FR16', 'System shall authenticate users via JWT (access + refresh tokens) with bcrypt hashing'],
        ['FR17', 'System shall support 3 user roles: admin (full), operator (monitoring), viewer (read-only)'],
        ['FR18', 'System shall allow runtime configuration of risk thresholds, AI confidence, alerts'],
        ['FR19', 'System shall record annotated video sessions as MP4 for later download'],
        ['FR20', 'System shall display density heatmap overlay on video stream when toggled'],
    ]
    story.append(make_table(['ID', 'Requirement'], frs, [avail*0.08, avail*0.92]))
    story.append(Paragraph('<b>Total: 20 functional requirements</b>', styles['Body']))

    # ---- 5. NON-FUNCTIONAL REQUIREMENTS ----
    story.append(Paragraph('5. Non-Functional Requirements', styles['SectionHead']))
    nfrs = [
        ['NFR1', 'System shall process video at 15 FPS with frame skip of 2 for real-time performance'],
        ['NFR2', 'System shall use SQLite for zero-configuration database deployment'],
        ['NFR3', 'System shall run on a single machine without external service dependencies'],
        ['NFR4', 'System shall use threading mode for SocketIO (no eventlet/gevent dependency)'],
        ['NFR5', 'All timestamps shall be stored in UTC and displayed in IST (UTC+5:30)'],
        ['NFR6', 'System shall persist metrics every 10 frames to balance storage vs. granularity'],
        ['NFR7', 'Alert notifications shall be sent in background threads (non-blocking)'],
        ['NFR8', 'YOLO input shall be resized to max 960px for GPU/CPU performance optimization'],
        ['NFR9', 'System shall auto-clean metrics older than 30 days and logs older than 90 days'],
        ['NFR10', 'Frontend shall use dark theme (bg #111318, accent #4f8ff7) with Bootstrap 5.3'],
        ['NFR11', 'All API endpoints shall require JWT authentication (except login and health check)'],
        ['NFR12', 'Export service shall handle up to 5,000 records per export without timeout'],
    ]
    story.append(make_table(['ID', 'Requirement'], nfrs, [avail*0.08, avail*0.92]))
    story.append(Paragraph('<b>Total: 12 non-functional requirements</b>', styles['Body']))

    # ---- 6. SYSTEM FEATURES ----
    story.append(PageBreak())
    story.append(Paragraph('6. System Features', styles['SectionHead']))

    # SF1
    story.append(Paragraph('SF1. AI Person Detection', styles['SubHead']))
    for b in [
        'YOLOv11s deep learning model (pre-trained on COCO dataset, class 0: person)',
        'BoT-SORT multi-object tracking with Kalman filtering',
        'Confidence threshold filtering (default: 0.25)',
        'IOU threshold filtering (default: 0.5)',
        'Minimum bounding box area filter (100px)',
        'Maximum aspect ratio filter (5.0)',
        'Dense crowd grid estimation with occlusion factor (1.3x) for 50+ people',
    ]:
        story.append(Paragraph(f'• {b}', styles['BulletCS']))

    # SF2
    story.append(Paragraph('SF2. Crowd Behavior Analysis (ML Layer)', styles['SubHead']))
    story.append(make_table(
        ['Algorithm', 'Purpose', 'Output'],
        [
            ['DBSCAN Clustering', 'Detect crowd groups', 'Cluster count, centers, sizes'],
            ['Proximity Analysis', 'Social distance monitoring', 'Pair alerts with distances'],
            ['Velocity Anomaly (z-score)', 'Detect abnormal movement', 'Fast movers / stationary flagged'],
            ['Flow Coherence', 'Stampede indicator', '0.0 (random) to 1.0 (stampede)'],
            ['Crowd Pressure', 'Crush risk estimation', '0.0 (safe) to 1.0 (dangerous)'],
            ['EMA Trend Prediction', 'Forecast density/risk', 'Increasing / Stable / Decreasing'],
        ],
        [avail*0.28, avail*0.35, avail*0.37]
    ))

    # SF3
    story.append(Paragraph('SF3. Risk Scoring Engine', styles['SubHead']))
    story.append(Paragraph(
        'Base = (0.4 × density_norm) + (0.3 × surge_norm) + (0.3 × velocity_inv_norm)<br/>'
        'ML Boosts: +max(0, pressure-0.3)×0.15 + max(0, coherence-0.5)×0.2<br/>'
        'Large crowd: ×1.15 if count &gt; 100. Final = clamp(0.0, 1.0)', styles['CodeCS']))
    story.append(make_table(
        ['Level', 'Score Range', 'Color', 'Action'],
        [
            ['SAFE', '0% - 24%', 'Green', 'Normal monitoring'],
            ['CAUTION', '25% - 49%', 'Yellow', 'Increased attention'],
            ['WARNING', '50% - 74%', 'Orange', 'Alert triggered, Telegram sent'],
            ['CRITICAL', '75% - 100%', 'Red', 'Immediate action, Telegram sent'],
        ],
        [avail*0.15, avail*0.15, avail*0.12, avail*0.58]
    ))

    # SF4
    story.append(Paragraph('SF4. Alert System', styles['SubHead']))
    for b in [
        'Threshold detection at WARNING and CRITICAL levels',
        '60-second cooldown per camera per risk level',
        '4 trigger types: extreme_density (&gt;6 p/m²), sudden_surge (&gt;0.8), stagnation_with_density, risk_threshold',
        'Database persistence with acknowledge/resolve workflow',
        'Multi-channel dispatch (SocketIO + Telegram)',
    ]:
        story.append(Paragraph(f'• {b}', styles['BulletCS']))

    # SF5
    story.append(Paragraph('SF5. Telegram Notifications', styles['SubHead']))
    for b in [
        'Zero-dependency implementation (Python stdlib urllib only)',
        'Photo attachment with annotated crowd frame',
        'Rich caption: risk level, camera name/location, trigger, all metrics',
        'IST formatted timestamps, background thread execution',
    ]:
        story.append(Paragraph(f'• {b}', styles['BulletCS']))

    # SF6
    story.append(Paragraph('SF6. Live Video Streaming', styles['SubHead']))
    story.append(Paragraph('MJPEG format at 15 FPS with 6-layer annotation system:', styles['Body']))
    for i, layer in enumerate([
        'Cluster outlines (convex hull)',
        'Proximity warning circles',
        'Flow direction arrows',
        'Per-person corner-style bounding boxes with ID + confidence',
        'HUD panel (top-left stats overlay)',
        'Sparkline chart (density + risk history)',
    ], 1):
        story.append(Paragraph(f'  {i}. {layer}', styles['BulletCS']))

    # SF7-SF15 condensed
    story.append(Paragraph('SF7. Density Heatmap', styles['SubHead']))
    story.append(Paragraph(
        'Gaussian blob accumulation at person centers, JET colormap (blue→red), toggleable overlay.', styles['Body']))

    story.append(Paragraph('SF8. Analytics Dashboard', styles['SubHead']))
    story.append(Paragraph(
        '4 time-series charts (Count, Density, Risk, Velocity), 6 summary cards, date range presets '
        '(1H/24H/7D/30D/All/Custom), collapsible data table, IST timestamps.', styles['Body']))

    story.append(Paragraph('SF9. Data Export', styles['SubHead']))
    story.append(make_table(
        ['Format', 'Library', 'Features'],
        [
            ['CSV', 'Python stdlib csv', 'Tabular data with all metric fields'],
            ['DOCX', 'python-docx', 'Professional report with summary + data table'],
            ['PDF', 'fpdf2', 'Color-coded risk levels, formatted layout'],
            ['Markdown', 'Python stdlib', 'GitHub-compatible tables'],
        ],
        [avail*0.15, avail*0.25, avail*0.6]
    ))

    story.append(Paragraph('SF10. User Management', styles['SubHead']))
    story.append(Paragraph(
        'JWT auth (HS256) with access + refresh tokens, bcrypt hashing (12 rounds), '
        '3 roles (admin/operator/viewer), CRUD, password reset, last login tracking.', styles['Body']))

    story.append(Paragraph('SF11. Settings Management', styles['SubHead']))
    story.append(Paragraph(
        'Runtime-configurable risk thresholds, alert channels, AI parameters. No restart required.', styles['Body']))

    story.append(Paragraph('SF12. Video Recording', styles['SubHead']))
    story.append(Paragraph(
        'Automatic recording during processing. Annotated MP4 output. Download via API.', styles['Body']))

    story.append(Paragraph('SF13. Real-Time Updates (SocketIO)', styles['SubHead']))
    story.append(Paragraph(
        'Live metrics broadcast (per-camera rooms + global), alert toasts, camera status events, '
        '5-second auto-refresh + event-driven updates.', styles['Body']))

    story.append(Paragraph('SF14. Camera Management', styles['SubHead']))
    story.append(Paragraph(
        'Multi-camera singleton registry, video upload with progress, shared AI engine, '
        'start/stop per camera, metadata (name, location, area, capacity, GPS).', styles['Body']))

    story.append(Paragraph('SF15. System Monitoring', styles['SubHead']))
    story.append(Paragraph(
        'Health check endpoint, system stats, log viewer, scheduled cleanup (30d metrics, 90d logs).', styles['Body']))
    story.append(Paragraph('<b>Total: 15 system features</b>', styles['Body']))

    # ---- 7. SYSTEM ARCHITECTURE ----
    story.append(PageBreak())
    story.append(Paragraph('7. System Architecture', styles['SectionHead']))
    story.append(Paragraph('Technology Stack', styles['SubHead']))
    story.append(make_table(
        ['Layer', 'Technology'],
        [
            ['Backend Framework', 'Flask 3.x'],
            ['Database', 'SQLite (via SQLAlchemy ORM)'],
            ['Real-Time', 'Flask-SocketIO (threading mode)'],
            ['AI/ML Model', 'YOLOv11s (Ultralytics)'],
            ['Object Tracking', 'BoT-SORT'],
            ['ML Analysis', 'scikit-learn (DBSCAN), NumPy'],
            ['Frontend', 'Jinja2 templates, Bootstrap 5.3 (dark theme)'],
            ['Charts', 'Chart.js 4.4.7'],
            ['Authentication', 'PyJWT + bcrypt'],
            ['Notifications', 'Telegram Bot API (urllib)'],
            ['Export', 'python-docx, fpdf2, csv (stdlib)'],
            ['Video Processing', 'OpenCV (headless)'],
        ],
        [avail*0.3, avail*0.7]
    ))

    story.append(Paragraph('Pipeline Flow', styles['SubHead']))
    pipeline = (
        'Video Input → VideoProcessor (background thread) → ai_engine.analyze_frame() '
        '[YOLO + BoT-SORT + velocity] → crowd_analyzer.analyze() [DBSCAN, proximity, anomaly, '
        'flow, pressure, EMA] → risk_calculator.calculate() [weighted score + ML boost + level] → '
        'ai_engine.annotate_frame() [6-layer annotations + heatmap] → Output [MJPEG stream, '
        'DB metrics, SocketIO broadcast, alert check, MP4 recording]'
    )
    story.append(Paragraph(pipeline, styles['CodeCS']))

    story.append(Paragraph('Key Files', styles['SubHead']))
    story.append(make_table(
        ['File', 'Purpose'],
        [
            ['app.py', 'Application entry point'],
            ['config.py', 'All configuration and thresholds'],
            ['backend/__init__.py', 'App factory, blueprint registration, defaults'],
            ['backend/services/ai_engine.py', 'YOLO + BoT-SORT + annotation rendering'],
            ['backend/services/crowd_analyzer.py', 'ML analysis layer'],
            ['backend/services/risk_calculator.py', 'Multi-factor risk scoring'],
            ['backend/services/video_processor.py', 'Background thread, MJPEG stream'],
            ['backend/services/camera_manager.py', 'Singleton camera registry'],
            ['backend/services/alert_manager.py', 'Alert creation, cooldown, dispatch'],
            ['backend/services/telegram_service.py', 'Telegram Bot API integration'],
            ['backend/services/export_service.py', 'CSV/DOCX/PDF/MD generation'],
        ],
        [avail*0.42, avail*0.58]
    ))

    # ---- 8. DATABASE MODELS ----
    story.append(PageBreak())
    story.append(Paragraph('8. Database Models', styles['SectionHead']))

    models = {
        'User': [
            ['id', 'Integer (PK)', 'Auto-increment'],
            ['username', 'String(50), unique', 'Login identifier'],
            ['email', 'String(120), unique', 'Email address'],
            ['password_hash', 'String(255)', 'bcrypt hashed password'],
            ['full_name', 'String(100)', 'Display name'],
            ['role', 'String(20)', 'admin / operator / viewer'],
            ['is_active', 'Boolean', 'Account enabled flag'],
            ['phone', 'String(20)', 'Contact number'],
            ['created_at', 'DateTime', 'Account creation (UTC)'],
            ['last_login', 'DateTime', 'Last login timestamp (UTC)'],
        ],
        'Camera': [
            ['id', 'String (PK)', 'UUID-based identifier'],
            ['name', 'String(100)', 'Display name'],
            ['location', 'String(200)', 'Physical location'],
            ['source_type', 'String(20)', 'rtsp / http / file / usb'],
            ['source_url', 'String(500)', 'Video source path or URL'],
            ['area_sqm', 'Float', 'Physical area covered (m²)'],
            ['expected_capacity', 'Integer', 'Max expected people'],
            ['is_active', 'Boolean', 'Camera enabled flag'],
            ['status', 'String(20)', 'online/offline/error/processing'],
            ['latitude, longitude', 'Float', 'GPS coordinates'],
        ],
        'Metric': [
            ['id', 'Integer (PK)', 'Auto-increment'],
            ['camera_id', 'String (FK)', 'Camera reference'],
            ['timestamp', 'DateTime (indexed)', 'Measurement time (UTC)'],
            ['count', 'Integer', 'People detected'],
            ['density', 'Float', 'People per m²'],
            ['avg_velocity', 'Float', 'Average speed (m/s)'],
            ['surge_rate', 'Float', 'Rate of count increase'],
            ['risk_score', 'Float', '0.0 - 1.0 risk value'],
            ['risk_level', 'String(20)', 'SAFE/CAUTION/WARNING/CRITICAL'],
            ['capacity_utilization', 'Float', '% of expected capacity'],
        ],
        'Alert': [
            ['id', 'Integer (PK)', 'Auto-increment'],
            ['alert_id', 'String(50), unique', 'Human-readable ID'],
            ['camera_id', 'String (FK)', 'Camera reference'],
            ['timestamp', 'DateTime (indexed)', 'Alert time (UTC)'],
            ['risk_level', 'String(20)', 'WARNING / CRITICAL'],
            ['trigger_condition', 'String(100)', 'What triggered alert'],
            ['message', 'Text', 'Human-readable message'],
            ['metrics_snapshot', 'Text (JSON)', 'Full metrics at alert time'],
            ['acknowledged', 'Boolean', 'Operator acknowledged'],
            ['resolved', 'Boolean', 'Alert resolved'],
        ],
        'Recording': [
            ['id', 'Integer (PK)', 'Auto-increment'],
            ['recording_id', 'String, unique', 'Human-readable ID'],
            ['camera_id', 'String (FK)', 'Camera reference'],
            ['start_time, end_time', 'DateTime', 'Recording duration'],
            ['duration_seconds', 'Float', 'Length in seconds'],
            ['frame_count', 'Integer', 'Total frames'],
            ['file_size_bytes', 'BigInteger', 'File size'],
        ],
        'Setting': [
            ['id', 'Integer (PK)', 'Auto-increment'],
            ['key', 'String, unique', 'Setting identifier'],
            ['value', 'Text', 'Setting value'],
            ['category', 'String', 'general/risk/alerts/ai'],
        ],
        'SystemLog': [
            ['id', 'Integer (PK)', 'Auto-increment'],
            ['timestamp', 'DateTime (indexed)', 'Log time (UTC)'],
            ['level', 'String (indexed)', 'info / warning / error'],
            ['component', 'String', 'Source module'],
            ['message', 'Text', 'Log message'],
        ],
    }
    for name, fields in models.items():
        story.append(Paragraph(name, styles['SubHead']))
        story.append(make_table(['Field', 'Type', 'Description'], fields,
                                [avail*0.25, avail*0.3, avail*0.45]))

    # ---- 9. API ENDPOINTS ----
    story.append(PageBreak())
    story.append(Paragraph('9. API Endpoints', styles['SectionHead']))

    api_groups = [
        ('Authentication (/api/auth) — 4 endpoints', [
            ['POST', '/api/auth/login', 'User login, returns JWT tokens'],
            ['POST', '/api/auth/logout', 'User logout'],
            ['POST', '/api/auth/refresh', 'Refresh access token'],
            ['GET', '/api/auth/me', 'Get current user info'],
        ]),
        ('Cameras (/api/cameras) — 9 endpoints', [
            ['GET', '/api/cameras', 'List all cameras with status'],
            ['POST', '/api/cameras', 'Create new camera'],
            ['GET', '/api/cameras/{id}', 'Get camera details'],
            ['PUT', '/api/cameras/{id}', 'Update camera settings'],
            ['DELETE', '/api/cameras/{id}', 'Delete camera'],
            ['POST', '/api/cameras/{id}/upload', 'Upload video file'],
            ['POST', '/api/cameras/{id}/start', 'Start AI processing'],
            ['POST', '/api/cameras/{id}/stop', 'Stop AI processing'],
            ['GET', '/api/cameras/{id}/stream', 'MJPEG video stream'],
        ]),
        ('Metrics (/api/metrics) — 6 endpoints', [
            ['GET', '/api/metrics/{id}', 'Get metrics (date-filterable)'],
            ['GET', '/api/metrics/{id}/current', 'Get latest live metrics'],
            ['GET', '/api/metrics/{id}/summary', 'Statistical summary'],
            ['GET', '/api/metrics/{id}/aggregate', 'Time-bucketed aggregates'],
            ['GET', '/api/metrics/{id}/export', 'Export CSV/DOCX/PDF/MD'],
            ['GET', '/api/metrics/summary', 'Global summary'],
        ]),
        ('Alerts (/api/alerts) — 5 endpoints', [
            ['GET', '/api/alerts', 'List alerts (filterable)'],
            ['GET', '/api/alerts/{id}', 'Get alert details'],
            ['POST', '/api/alerts/{id}/acknowledge', 'Acknowledge alert'],
            ['POST', '/api/alerts/{id}/resolve', 'Resolve alert'],
            ['GET', '/api/alerts/unacknowledged/count', 'Count open alerts'],
        ]),
        ('Recordings (/api/recordings) — 4 endpoints', [
            ['GET', '/api/recordings', 'List recordings'],
            ['GET', '/api/recordings/{id}', 'Get recording details'],
            ['GET', '/api/recordings/{id}/download', 'Download file'],
            ['DELETE', '/api/recordings/{id}', 'Delete recording'],
        ]),
        ('Settings (/api/settings) — 3 endpoints', [
            ['GET', '/api/settings/{category}', 'Get settings by category'],
            ['PUT', '/api/settings/{cat}/{key}', 'Update a setting'],
            ['POST', '/api/settings/risk-thresholds', 'Bulk update thresholds'],
        ]),
        ('Users (/api/users) — 5 endpoints', [
            ['GET', '/api/users', 'List all users'],
            ['POST', '/api/users', 'Create new user'],
            ['PUT', '/api/users/{id}', 'Update user'],
            ['DELETE', '/api/users/{id}', 'Delete user'],
            ['POST', '/api/users/{id}/reset-password', 'Reset password'],
        ]),
        ('System (/api/system) — 3 endpoints', [
            ['GET', '/api/system/health', 'Health check'],
            ['GET', '/api/system/stats', 'System statistics'],
            ['GET', '/api/system/logs', 'View system logs'],
        ]),
    ]
    for title, rows in api_groups:
        story.append(Paragraph(title, styles['SubHead']))
        story.append(make_table(['Method', 'Endpoint', 'Description'], rows,
                                [avail*0.1, avail*0.4, avail*0.5]))
    story.append(Paragraph('<b>Total: 39 API endpoints</b>', styles['Body']))

    # ---- 10. REAL-TIME EVENTS ----
    story.append(PageBreak())
    story.append(Paragraph('10. Real-Time Events (SocketIO)', styles['SectionHead']))
    story.append(Paragraph('Client to Server', styles['SubHead']))
    story.append(make_table(
        ['Event', 'Payload', 'Description'],
        [
            ['subscribe_camera', '{camera_id}', 'Join camera-specific room'],
            ['unsubscribe_camera', '{camera_id}', 'Leave camera-specific room'],
            ['get_metrics', '{camera_id}', 'Request latest metrics'],
        ],
        [avail*0.25, avail*0.25, avail*0.5]
    ))
    story.append(Paragraph('Server to Client', styles['SubHead']))
    story.append(make_table(
        ['Event', 'Payload', 'Description'],
        [
            ['metrics_update', 'Full metrics object', 'Real-time metrics broadcast'],
            ['alert', 'Alert object', 'New alert notification'],
            ['camera_status', '{camera_id, status}', 'Camera status change'],
            ['system_notification', '{type, message}', 'System messages'],
        ],
        [avail*0.25, avail*0.25, avail*0.5]
    ))

    # ---- 11. NOTIFICATION CHANNELS ----
    story.append(Paragraph('11. Notification Channels', styles['SectionHead']))
    story.append(make_table(
        ['Channel', 'Status', 'Trigger Level', 'Details'],
        [
            ['Dashboard (SocketIO)', 'Active', 'WARNING, CRITICAL', 'Toast notifications, alert badge, live metrics'],
            ['Telegram Bot', 'Active', 'WARNING, CRITICAL', 'Photo + caption with full metrics, IST timestamps'],
            ['Email (SMTP)', 'Not implemented', '-', 'Toggle exists in settings'],
            ['SMS (Twilio)', 'Not implemented', '-', 'Toggle exists in settings'],
        ],
        [avail*0.2, avail*0.15, avail*0.2, avail*0.45]
    ))

    # ---- 12. CONFIGURATION REFERENCE ----
    story.append(Paragraph('12. Configuration Reference', styles['SectionHead']))

    config_groups = [
        ('AI / Detection', [
            ['YOLO_MODEL', 'yolo11s.pt', 'YOLO model file'],
            ['YOLO_CONFIDENCE', '0.25', 'Detection confidence threshold'],
            ['YOLO_IOU', '0.5', 'IOU threshold'],
            ['YOLO_IMGSZ', '960', 'Input image size (px)'],
            ['YOLO_MIN_BOX_AREA', '100', 'Min bounding box area (px)'],
            ['YOLO_MAX_BOX_RATIO', '5.0', 'Max aspect ratio filter'],
        ]),
        ('ML / Crowd Analysis', [
            ['PROXIMITY_THRESHOLD_PX', '80', 'Proximity alert distance (px)'],
            ['CLUSTER_EPS_PX', '120', 'DBSCAN epsilon (px)'],
            ['CLUSTER_MIN_SAMPLES', '2', 'DBSCAN min cluster size'],
            ['ANOMALY_VELOCITY_ZSCORE', '2.0', 'Z-score threshold'],
            ['COHERENCE_WINDOW', '10', 'Flow window (frames)'],
        ]),
        ('Risk Scoring', [
            ['RISK_WEIGHT_DENSITY', '0.4', 'Density weight'],
            ['RISK_WEIGHT_SURGE', '0.3', 'Surge rate weight'],
            ['RISK_WEIGHT_VELOCITY', '0.3', 'Velocity weight'],
            ['DENSITY_WARNING', '6.0', 'WARNING density level'],
            ['DENSITY_CRITICAL', '6.0', 'CRITICAL density level'],
            ['VELOCITY_STAGNANT', '0.2', 'Stagnant threshold (m/s)'],
        ]),
        ('Processing', [
            ['PROCESS_FPS', '15', 'Target processing FPS'],
            ['FRAME_SKIP', '2', 'Process every Nth frame'],
            ['ALERT_COOLDOWN', '60', 'Seconds between alerts'],
        ]),
    ]
    for title, rows in config_groups:
        story.append(Paragraph(title, styles['SubHead']))
        story.append(make_table(['Parameter', 'Default', 'Description'], rows,
                                [avail*0.35, avail*0.12, avail*0.53]))

    # ---- 13. DEFAULT DATA ----
    story.append(Paragraph('13. Default Data', styles['SectionHead']))
    story.append(Paragraph('Default Admin Account', styles['SubHead']))
    story.append(make_table(
        ['Field', 'Value'],
        [['Username', 'admin'], ['Password', 'admin123'],
         ['Email', 'admin@crowdsafe.local'], ['Role', 'admin']],
        [avail*0.3, avail*0.7]
    ))
    story.append(Paragraph('Default Settings', styles['SubHead']))
    story.append(make_table(
        ['Category', 'Key', 'Default Value'],
        [
            ['general', 'app_name', 'CrowdSafe'],
            ['general', 'timezone', 'UTC'],
            ['general', 'theme', 'dark'],
            ['risk', 'density_warning', '4.0'],
            ['risk', 'density_critical', '6.0'],
            ['risk', 'velocity_stagnant', '0.2'],
            ['risk', 'weight_density / surge / velocity', '0.4 / 0.3 / 0.3'],
            ['alerts', 'cooldown_seconds', '60'],
            ['alerts', 'telegram_enabled', 'true'],
            ['ai', 'model', 'yolo11n.pt'],
            ['ai', 'confidence', '0.5'],
            ['ai', 'iou', '0.7'],
        ],
        [avail*0.18, avail*0.4, avail*0.42]
    ))

    # ---- 14. SUMMARY STATISTICS ----
    story.append(Paragraph('14. Summary Statistics', styles['SectionHead']))
    story.append(make_table(
        ['Category', 'Count'],
        [
            ['Scope Items', '12'],
            ['Functional Requirements', '20'],
            ['Non-Functional Requirements', '12'],
            ['System Features', '15'],
            ['API Endpoints', '39'],
            ['Database Models', '7'],
            ['Backend Services', '9'],
            ['Frontend Pages', '7'],
            ['SocketIO Events', '7'],
            ['Export Formats', '4'],
            ['Notification Channels', '4'],
            ['Configuration Options', '40+'],
            ['ML Algorithms', '6'],
            ['Annotation Layers', '6'],
        ],
        [avail*0.6, avail*0.4]
    ))

    # Build
    doc.build(story)
    print('SRS.pdf generated successfully.')


if __name__ == '__main__':
    build_pdf()
