from flask import Blueprint, abort, jsonify, request
from flask_jwt_extended import create_access_token
from pydantic import ValidationError

from app.extensions import db
from app.models import User

from .schemas import (
    LoginRequest,
    UserCreate,
    UserOut,
)

bp = Blueprint("auth", __name__)


@bp.post("/register")
def register():
    """Create a new client account from an email, a password and a name."""
    try:
        data = UserCreate.model_validate(request.get_json())
    except ValidationError as e:
        abort(400, str(e))

    if User.query.filter_by(email=data.email).first():
        abort(409, "Email already registered")

    user = User(email=data.email, name=data.name)
    user.password = data.password
    db.session.add(user)
    db.session.commit()
    return UserOut.model_validate(user).model_dump(mode="json"), 201


@bp.post("/login")
def login():
    """Check credentials and hand back a JWT access token."""
    try:
        data = LoginRequest.model_validate(request.get_json())
    except ValidationError as e:
        abort(400, str(e))

    user = User.query.filter_by(email=data.email).first()
    if not user or not user.check_password(data.password):
        abort(401, "Invalid email or password")

    token = create_access_token(identity=str(user.id))
    return jsonify({"access_token": token})
