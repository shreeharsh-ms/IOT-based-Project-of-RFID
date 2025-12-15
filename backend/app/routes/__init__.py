from .scan_routes import scan_bp
from .fine_routes import fine_bp
from .admin_routes import admin_bp
from .home_routes import home_bp
from .user_routes import user_bp

def register_routes(app):
    app.register_blueprint(scan_bp, url_prefix="/api/scan")
    app.register_blueprint(fine_bp, url_prefix="/api/fine")
    app.register_blueprint(admin_bp, url_prefix="/api/admin")
    app.register_blueprint(user_bp, url_prefix="/api/user")
    app.register_blueprint(home_bp)  # No prefix for home routes
