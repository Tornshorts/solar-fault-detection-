import re
from flask import request, jsonify, Blueprint, render_template
from services import database

# Blueprint for API routes (prefix: /api)
alert_bp = Blueprint("alert", __name__, url_prefix="/api")

# Blueprint for page routes (no prefix)
page_bp = Blueprint("page", __name__)


def parse_serial_line(line):
    """
    Parse a plain-text serial line from the ESP.
    Expected format: V: 2.42V | I: 510mA | L: 16% | T: 26.9C
    Returns a dict with voltage, current, load, temperature, and status.
    """
    result = {}

    # Extract voltage  (e.g. "V: 2.42V")
    v_match = re.search(r'V:\s*([\d.]+)V', line)
    if v_match:
        result["voltage"] = float(v_match.group(1))

    # Extract current in mA  (e.g. "I: 510mA")
    i_match = re.search(r'I:\s*([\d.]+)mA', line)
    if i_match:
        result["current"] = float(i_match.group(1))

    # Extract load percentage  (e.g. "L: 16%")
    l_match = re.search(r'L:\s*([\d.]+)%', line)
    if l_match:
        result["load"] = float(l_match.group(1))

    # Extract temperature  (e.g. "T: 26.9C")
    t_match = re.search(r'T:\s*([\d.]+)C', line)
    if t_match:
        result["temperature"] = float(t_match.group(1))

    # Auto-determine status based on readings
    result["status"] = determine_status(result)

    return result


def determine_status(data):
    """Determine panel status based on sensor readings."""
    voltage = data.get("voltage", 0)
    current = data.get("current", 0)
    temperature = data.get("temperature", 0)
    load = data.get("load", 0)

    faults = []

    # Voltage checks
    if voltage > 5.5:
        faults.append("OVER_VOLTAGE")
    elif voltage < 1.0:
        faults.append("LOW_VOLTAGE")

    # Temperature checks
    if temperature > 60:
        faults.append("OVER_TEMP")
    elif temperature > 45:
        faults.append("HIGH_TEMP")

    # Current checks
    if current > 1000:
        faults.append("OVER_CURRENT")

    # Load checks
    if load < 5:
        faults.append("LOW_LOAD")

    if faults:
        return " | ".join(faults)
    return "HEALTHY"


def normalize_json(raw):
    """
    Map ESP JSON keys to internal field names.
    ESP sends:  panel_voltage_v, current_ma, light_pct, temp_c, device, ip
    Internal:   voltage, current, load, temperature, device, ip
    """
    field_map = {
        "panel_voltage_v": "voltage",
        "current_ma":      "current",
        "light_pct":       "load",
        "temp_c":          "temperature",
    }
    normalized = {}
    for key, value in raw.items():
        new_key = field_map.get(key, key)  # rename or keep as-is
        normalized[new_key] = value
    return normalized


@alert_bp.route("/data", methods=["POST"])
def receive_data():
    """
    Accepts data in two formats:
    1. Plain text from ESP serial: V: 2.42V | I: 510mA | L: 16% | T: 26.9C
    2. JSON from ESP HTTP:
       {"panel_voltage_v": 12.34, "current_ma": 210, "light_pct": 76,
        "temp_c": 29.1, "device": "esp8266", "ip": "192.168.1.55"}
    """
    content_type = request.content_type or ""

    if "application/json" in content_type:
        raw = request.get_json()
        data = normalize_json(raw)
    else:
        # Plain text mode — parse the serial line
        raw_text = request.get_data(as_text=True).strip()
        print(f"📡 RAW SERIAL DATA: {raw_text}")

        lines = [l.strip() for l in raw_text.splitlines() if l.strip()]
        if not lines:
            return jsonify({"error": "Empty data received"}), 400

        data = parse_serial_line(lines[-1])

    # Add a default panel_id if not present
    if "panel_id" not in data:
        data["panel_id"] = data.get("device", "PANEL-1")

    # Auto-determine status
    if "status" not in data:
        data["status"] = determine_status(data)

    print("📡 PARSED DATA:", data)

    # Persist to database
    try:
        database.insert_alert(data)
    except Exception as e:
        print("Error inserting alert:", e)
        return jsonify({"error": str(e)}), 500

    return jsonify({
        "message": "Data received",
        "received": data
    }), 200


@alert_bp.route("/alerts", methods=["GET"])
def get_alerts():
    rows = database.get_recent_alerts(50)
    # rows: list of tuples (panel_id, voltage, current, load, temperature, status, timestamp)
    alerts = []
    for r in rows:
        alerts.append({
            "panel_id": r[0],
            "voltage": r[1],
            "current": r[2],
            "load": r[3],
            "temperature": r[4],
            "status": r[5],
            "timestamp": r[6]
        })
    return jsonify({"alerts": alerts}), 200


@page_bp.route("/")
def dashboard():
    return render_template("dashboard.html")
