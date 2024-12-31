import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask
from flask_jwt_extended import JWTManager

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

    return app


if __name__ == "__main__":
    app = create_app(Config)
    app.run(port=os.getenv("FLASK_PORT"), host=os.getenv("FLASK_HOST"))
