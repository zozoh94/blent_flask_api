from functools import wraps

from flask_jwt_extended import get_jwt_identity, jwt_required

from app.extensions import db
from app.models import User


def admin_required(fn):
    @wraps(fn)
    @jwt_required()
    def wrapper(*args, **kwargs):
        user = db.session.get(User, int(get_jwt_identity()))
        if user is None or user.role != "admin":
            return {"error": "Admin privileges required"}, 403
        return fn(*args, **kwargs)

    return wrapper
