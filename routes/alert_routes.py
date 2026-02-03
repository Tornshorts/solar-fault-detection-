from flask import request, jsonify, Blueprint, render_template
from services import database

# Blueprint for API routes (prefix: /api)
alert_bp = Blueprint("alert", __name__, url_prefix="/api")

# Blueprint for page routes (no prefix)
page_bp = Blueprint("page", __name__)


@alert_bp.route("/data", methods=["POST"])
def receive_data():
    data = request.get_json()

    print("📡 RAW DATA FROM ESP8266:")
    print(data)

    # Persist to database
    try:
        database.insert_alert(data)
    except Exception as e:
        print("Error inserting alert:", e)

    return jsonify({
        "message": "Data received",
        "received": data
    }), 200


@alert_bp.route("/alerts", methods=["GET"])
def get_alerts():
    rows = database.get_recent_alerts(50)
    # rows: list of tuples (panel_id, voltage, current, temperature, status, timestamp)
    alerts = []
    for r in rows:
        alerts.append({
            "panel_id": r[0],
            "voltage": r[1],
            "current": r[2],
            "temperature": r[3],
            "status": r[4],
            "timestamp": r[5]
        })
    return jsonify({"alerts": alerts}), 200


@page_bp.route("/")
def dashboard():
    return render_template("dashboard.html")
