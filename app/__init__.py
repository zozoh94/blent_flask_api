from flask import Flask

from app.extensions import db, jwt

__all__ = ["create_app", "db"]


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)

    app.config.from_object("app.config.DefaultConfig")
    if test_config is not None:
        app.config.update(test_config)

    db.init_app(app)
    jwt.init_app(app)

    from app.auth.routes import bp as auth_bp
    from app.product.routes import bp as product_bp

    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(product_bp, url_prefix="/api/products")

    from app.commands import register_commands

    register_commands(app)

    with app.app_context():
        from app import models  # noqa: F401

    return app
