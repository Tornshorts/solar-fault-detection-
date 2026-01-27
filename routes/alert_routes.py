#Receives esp data and stores in sqlite
from flask import request,jsonify, Blueprint
from services.database import insert_alert

alert_bp=Blueprint("alert",__name__)

@alert_bp.route("/alert", methods=["POST"])
def receive_alert():
    data = request.get_json()

    if not data:
        return jsonify({"error":"Invalid JSON"}),400
    
    insert_alert(data)
    return jsonify({"message":"Allert stored"}),200
