# import os
# import sys
# from pathlib import Path

# from flask import Flask, redirect, url_for
# from flask_login import current_user
# from flask_jwt_extended import JWTManager
# from datetime import timedelta

# from dotenv import load_dotenv

# from login import login_manager

# sys.path.append(str(Path(__file__).parent.parent))
# sys.path.append(str(Path(__file__).parent))

# load_dotenv()
# from config import Config  # noqa: E402
# from models import db  # noqa: E402

# from blueprints.api import bp as bp_api  # noqa: E402


# def create_app(config_class=Config) -> Flask:
#     template_dir = Path(__file__).parent / "templates"
#     static_dir = Path(__file__).parent / "static"
#     app = Flask(__name__, template_folder=template_dir, static_folder=static_dir)
#     app.config.from_object(config_class)
#     db.init_app(app)
#     # login_manager.init_app(app)

#     # Configure JWT
#     app.config["JWT_SECRET_KEY"] = os.environ.get(
#         "JWT_SECRET_KEY", "your-secret-key"
#     )  # Change in production
#     app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=1)
#     jwt = JWTManager(app)

#     app.register_blueprint(bp_api, url_prefix="/api")

#     @app.route("/", methods=["GET", "POST"])
#     def index():
#         # if not current_user.is_authenticated:
#         #     return redirect(url_for("login.login"))
#         # return redirect(url_for("my-deliverables.index"))
#         return redirect(url_for("main.index"))

#     return app


# if __name__ == "__main__":
#     app = create_app(Config)
#     app.run(port=os.getenv("FLASK_PORT"), host=os.getenv("FLASK_HOST"))
