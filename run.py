from flask import Flask
from routes.alert_routes import alert_bp, page_bp
from services.database import init_db

app = Flask(__name__)

# Register blueprints
app.register_blueprint(alert_bp)  # API routes at /api/*
app.register_blueprint(page_bp)   # Page routes at /


if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=3000, debug=True)