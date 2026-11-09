from flask_jwt_extended import JWTManager
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
jwt = JWTManager()


@jwt.user_lookup_loader
def load_user(_, jwt_data):
    from app.models import User

    return db.session.get(User, int(jwt_data["sub"]))
