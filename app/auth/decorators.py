from functools import wraps

from flask import abort
from flask_jwt_extended import current_user, jwt_required


def admin_required(fn):
    @wraps(fn)
    @jwt_required()
    def wrapper(*args, **kwargs):
        if current_user.role != "admin":
            abort(403, "Admin privileges required")
        return fn(*args, **kwargs)

    return wrapper
