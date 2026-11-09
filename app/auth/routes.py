from flask import Blueprint, abort, jsonify, request
from flask_jwt_extended import create_access_token
from pydantic import ValidationError
from spectree import Response

from app.extensions import api, db
from app.models import User

from .schemas import (
    LoginRequest,
    TokenOut,
    UserCreate,
    UserOut,
)

bp = Blueprint("auth", __name__)


@bp.post("/register")
@api.validate(
    json=UserCreate,
    resp=Response("HTTP_400", "HTTP_409", HTTP_201=UserOut),
    tags=["auth"],
    skip_validation=True,
)
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
@api.validate(
    json=LoginRequest,
    resp=Response("HTTP_400", "HTTP_401", HTTP_200=TokenOut),
    tags=["auth"],
    skip_validation=True,
)
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
