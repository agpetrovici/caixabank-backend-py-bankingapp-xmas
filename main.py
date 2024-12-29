import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask, current_app, request, redirect
from flask_jwt_extended import JWTManager
from werkzeug.middleware.proxy_fix import ProxyFix

sys.path.append(str(Path(__file__).parent.parent))
sys.path.append(str(Path(__file__).parent))

load_dotenv()
from app.blueprints.api import bp as bp_api  # noqa: E402
from app.config import Config  # noqa: E402
from app.models import db  # noqa: E402
from app.utils.utils_email import mail  # noqa: E402


def create_app(config_class=Config) -> Flask:
    template_dir = Path(__file__).parent / "templates"
    static_dir = Path(__file__).parent / "static"
    app = Flask(__name__, template_folder=template_dir, static_folder=static_dir)
    app.config.from_object(config_class)

    # Add ProxyFix middleware
    app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1)

    db.init_app(app)

    JWTManager(app)

    # Email configuration for MailHog
    app.config.update(
        MAIL_SERVER=os.getenv("MAIL_SERVER", "smtp"),  # MailHog container name
        MAIL_PORT=int(os.getenv("MAIL_PORT", 1025)),  # MailHog SMTP port
        MAIL_USE_TLS=False,  # MailHog doesn't use TLS
        MAIL_DEFAULT_SENDER="Financial App <noreply@finapp.com>",
    )
    mail.init_app(app)

    # Blueprint registration
    app.register_blueprint(bp_api, url_prefix="/api")

    # Create all tables
    with app.app_context():
        db.create_all()

    # Force HTTPS
    @app.before_request
    def force_https():
        if not request.is_secure and not current_app.debug:
            url = request.url.replace("http://", "https://", 1)
            return redirect(url, code=301)

    # Add security headers
    @app.after_request
    def add_security_headers(response):
        for header, value in current_app.config["SECURE_HEADERS"].items():
            response.headers[header] = value
        return response

    return app


if __name__ == "__main__":
    app = create_app(Config)
    app.run(
        ssl_context=("app/certs/cert.pem", "app/certs/key.pem"),
        port=os.getenv("FLASK_PORT"),
        host=os.getenv("FLASK_HOST"),
    )
