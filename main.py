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

cert_path = Path("app/certs/cert.pem")
key_path = Path("app/certs/key.pem")


def create_app(config_class=Config) -> Flask:
    template_dir = Path(__file__).parent / "templates"
    static_dir = Path(__file__).parent / "static"
    app = Flask(__name__, template_folder=template_dir, static_folder=static_dir)
    app.config.from_object(config_class)

    # Configure SSL context if certificates exist
    if cert_path.exists() and key_path.exists():
        app.config["SSL_CERTIFICATE"] = str(cert_path)
        app.config["SSL_KEY"] = str(key_path)

    # Add ProxyFix middleware
    app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1)

    db.init_app(app)
    JWTManager(app)

    # Email configuration for MailHog
    app.config.update(
        MAIL_SERVER=os.getenv("MAIL_SERVER", "smtp"),
        MAIL_PORT=int(os.getenv("MAIL_PORT", 1025)),
        MAIL_USE_TLS=False,
        MAIL_DEFAULT_SENDER="Financial App <noreply@finapp.com>",
    )
    mail.init_app(app)

    app.register_blueprint(bp_api, url_prefix="/api")

    with app.app_context():
        db.create_all()

    @app.before_request
    def force_https():
        if not request.is_secure and not current_app.debug:
            url = request.url.replace("http://", "https://", 1)
            return redirect(url, code=301)

    @app.after_request
    def add_security_headers(response):
        for header, value in current_app.config["SECURE_HEADERS"].items():
            response.headers[header] = value
        return response

    return app


app = create_app(Config)

if __name__ == "__main__":
    ssl_context = None
    if cert_path.exists() and key_path.exists():
        ssl_context = (str(cert_path), str(key_path))

    app.run(
        ssl_context=ssl_context,
        port=int(os.getenv("FLASK_PORT", 3000)),
        host=os.getenv("FLASK_HOST", "0.0.0.0"),
    )
