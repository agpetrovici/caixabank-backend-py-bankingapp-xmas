from flask import Blueprint

from app.utils.utils_auth import create, authenticate, handle_auth_operation

bp = Blueprint("auth", __name__, url_prefix="/api/auth")


@bp.route("/register", methods=["POST"])
def register():
    return handle_auth_operation(create)


@bp.route("/login", methods=["POST"])
def login():
    return handle_auth_operation(authenticate)
