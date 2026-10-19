from flask import Blueprint, jsonify, request
from flask_jwt_extended import create_access_token
from pydantic import ValidationError

from app.extensions import db
from app.models import User
from app.schemas.users import (
    LoginRequest,
    UserCreate,
    UserOut,
)  # adjust to your class names

bp = Blueprint("auth", __name__)


@bp.post("/register")
def register():
    """Create a new client account from an email, a password and a name."""
    try:
        data = UserCreate.model_validate(request.get_json())
    except ValidationError as e:
        return jsonify({"error": str(e)}), 400

    if User.query.filter_by(email=data.email).first():
        return jsonify({"error": "Email already registered"}), 409

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
        return jsonify({"error": str(e)}), 400

    user = User.query.filter_by(email=data.email).first()
    if not user or not user.check_password(data.password):
        return jsonify({"error": "Invalid email or password"}), 401

    token = create_access_token(identity=str(user.id))
    return jsonify({"access_token": token})
