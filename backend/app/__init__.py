from flask import Flask
from flask_cors import CORS
from .config import Config
from .extensions import mongo
from .routes import register_routes

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    mongo.init_app(app)

    # 🔥 FULL CORS CONFIG (fixes OPTIONS + Authorization)
    CORS(
        app,
        resources={r"/api/*": {"origins": [
            "http://127.0.0.1:5501",
            "http://localhost:5501"
        ]}},
        supports_credentials=True,
        allow_headers=["Content-Type", "Authorization"],
        methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"]
    )

    register_routes(app)
    return app
