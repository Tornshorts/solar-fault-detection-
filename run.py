from flask import Flask
from routes.alert_routes import alert_bp
from services.database import init_db

app=Flask(__name__)

app.register_blueprint(alert_bp)
if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000, debug = True)