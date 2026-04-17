from flask import Blueprint, request, jsonify, Response
from backend.models.metric import Metric
from backend.models.camera import Camera
from backend.services.camera_manager import camera_manager
from datetime import datetime, timedelta, timezone
from sqlalchemy import func

metrics_bp = Blueprint('metrics', __name__)


def _parse_dt(val):
    """Parse ISO datetime string to datetime object."""
    if not val:
        return None
    try:
        return datetime.fromisoformat(val.replace('Z', '+00:00'))
    except (ValueError, TypeError):
        return None


def _build_query(camera_id, start=None, end=None):
    """Build filtered query for a camera's metrics."""
    q = Metric.query.filter_by(camera_id=camera_id)
    if start:
        q = q.filter(Metric.timestamp >= start)
    if end:
        q = q.filter(Metric.timestamp <= end)
    return q


@metrics_bp.route('/<camera_id>', methods=['GET'])
def get_metrics(camera_id):
    limit = request.args.get('limit', 100, type=int)
    start = _parse_dt(request.args.get('start'))
    end = _parse_dt(request.args.get('end'))

    q = _build_query(camera_id, start, end)
    q = q.order_by(Metric.timestamp.desc()).limit(limit)
    metrics = q.all()
    return jsonify([m.to_dict() for m in reversed(metrics)])


@metrics_bp.route('/<camera_id>/current', methods=['GET'])
def get_current(camera_id):
    proc = camera_manager.get_processor(camera_id)
    if proc and proc.is_running:
        return jsonify(proc.latest_metrics)
    metric = (Metric.query.filter_by(camera_id=camera_id)
              .order_by(Metric.timestamp.desc()).first())
    return jsonify(metric.to_dict() if metric else {})


@metrics_bp.route('/<camera_id>/summary', methods=['GET'])
def get_camera_summary(camera_id):
    start = _parse_dt(request.args.get('start'))
    end = _parse_dt(request.args.get('end'))

    q = _build_query(camera_id, start, end)
    row = q.with_entities(
        func.avg(Metric.density).label('avg_density'),
        func.max(Metric.count).label('peak_count'),
        func.avg(Metric.count).label('avg_count'),
        func.max(Metric.risk_score).label('max_risk'),
        func.avg(Metric.avg_velocity).label('avg_velocity'),
        func.avg(Metric.risk_score).label('avg_risk'),
        func.max(Metric.density).label('max_density'),
        func.count(Metric.id).label('total_records'),
    ).first()

    return jsonify({
        'avg_density': round(row.avg_density or 0, 3),
        'peak_count': row.peak_count or 0,
        'avg_count': round(row.avg_count or 0, 1),
        'max_risk_score': round(row.max_risk or 0, 3),
        'avg_velocity': round(row.avg_velocity or 0, 2),
        'avg_risk': round(row.avg_risk or 0, 3),
        'max_density': round(row.max_density or 0, 3),
        'total_records': row.total_records or 0,
    })


@metrics_bp.route('/<camera_id>/aggregate', methods=['GET'])
def get_aggregate(camera_id):
    """Aggregate metrics by time interval (hourly/daily/weekly)."""
    start = _parse_dt(request.args.get('start'))
    end = _parse_dt(request.args.get('end'))
    interval = request.args.get('interval', 'hourly')

    # SQLite strftime patterns
    fmt_map = {
        'hourly': '%Y-%m-%d %H:00',
        'daily': '%Y-%m-%d',
        'weekly': '%Y-W%W',
    }
    fmt = fmt_map.get(interval, '%Y-%m-%d %H:00')

    q = _build_query(camera_id, start, end)
    time_bucket = func.strftime(fmt, Metric.timestamp).label('bucket')

    rows = (q.with_entities(
        time_bucket,
        func.avg(Metric.count).label('avg_count'),
        func.max(Metric.count).label('max_count'),
        func.avg(Metric.density).label('avg_density'),
        func.max(Metric.density).label('max_density'),
        func.avg(Metric.avg_velocity).label('avg_velocity'),
        func.avg(Metric.risk_score).label('avg_risk'),
        func.max(Metric.risk_score).label('max_risk'),
        func.count(Metric.id).label('sample_count'),
    ).group_by(time_bucket)
     .order_by(time_bucket)
     .all())

    result = []
    for r in rows:
        result.append({
            'bucket': r.bucket,
            'avg_count': round(r.avg_count or 0, 1),
            'max_count': r.max_count or 0,
            'avg_density': round(r.avg_density or 0, 3),
            'max_density': round(r.max_density or 0, 3),
            'avg_velocity': round(r.avg_velocity or 0, 2),
            'avg_risk': round(r.avg_risk or 0, 3),
            'max_risk': round(r.max_risk or 0, 3),
            'sample_count': r.sample_count or 0,
        })

    return jsonify(result)


@metrics_bp.route('/<camera_id>/export', methods=['GET'])
def export_metrics(camera_id):
    """Export metrics as CSV, DOCX, PDF, or MD."""
    fmt = request.args.get('format', 'csv').lower()
    start = _parse_dt(request.args.get('start'))
    end = _parse_dt(request.args.get('end'))
    limit = request.args.get('limit', 5000, type=int)

    # Get camera name
    cam = Camera.query.get(camera_id)
    camera_name = cam.name if cam else camera_id

    # Fetch metrics
    q = _build_query(camera_id, start, end)
    records = q.order_by(Metric.timestamp.asc()).limit(limit).all()
    metrics = [m.to_dict() for m in records]

    # Compute summary
    summary_q = _build_query(camera_id, start, end)
    row = summary_q.with_entities(
        func.avg(Metric.density).label('avg_density'),
        func.max(Metric.count).label('peak_count'),
        func.avg(Metric.count).label('avg_count'),
        func.max(Metric.risk_score).label('max_risk'),
    ).first()
    summary = {
        'avg_density': round(row.avg_density or 0, 3),
        'peak_count': row.peak_count or 0,
        'avg_count': round(row.avg_count or 0, 1),
        'max_risk_score': round(row.max_risk or 0, 3),
    }

    from backend.services.export_service import (
        export_csv, export_docx, export_pdf, export_markdown
    )

    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename_base = f'crowdsafe_{camera_name}_{ts}'

    if fmt == 'csv':
        data = export_csv(metrics, summary)
        return Response(
            data,
            mimetype='text/csv',
            headers={'Content-Disposition': f'attachment; filename="{filename_base}.csv"'}
        )
    elif fmt == 'docx':
        data = export_docx(metrics, summary, camera_name)
        return Response(
            data,
            mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document',
            headers={'Content-Disposition': f'attachment; filename="{filename_base}.docx"'}
        )
    elif fmt == 'pdf':
        data = export_pdf(metrics, summary, camera_name)
        return Response(
            data,
            mimetype='application/pdf',
            headers={'Content-Disposition': f'attachment; filename="{filename_base}.pdf"'}
        )
    elif fmt == 'md':
        data = export_markdown(metrics, summary, camera_name)
        return Response(
            data.encode('utf-8'),
            mimetype='text/markdown',
            headers={'Content-Disposition': f'attachment; filename="{filename_base}.md"'}
        )
    else:
        return jsonify({'error': f'Unsupported format: {fmt}'}), 400


@metrics_bp.route('/summary', methods=['GET'])
def get_global_summary():
    status = camera_manager.get_all_status()
    total_people = 0
    cameras_active = 0
    max_risk = 0.0
    max_risk_level = 'SAFE'
    for info in status.values():
        if info['running']:
            cameras_active += 1
            m = info['metrics']
            total_people += m.get('count', 0)
            if m.get('risk_score', 0) > max_risk:
                max_risk = m['risk_score']
                max_risk_level = m.get('risk_level', 'SAFE')
    return jsonify({
        'total_people': total_people,
        'cameras_active': cameras_active,
        'max_risk_score': round(max_risk, 3),
        'max_risk_level': max_risk_level,
    })
