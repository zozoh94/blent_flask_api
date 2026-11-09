from flask import Flask

from app.extensions import api, db, jwt

__all__ = ["create_app", "db"]


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)
    app.json.ensure_ascii = False

    app.config.from_object("app.config.DefaultConfig")
    if test_config is not None:
        app.config.update(test_config)

    db.init_app(app)
    jwt.init_app(app)

    from app.auth.routes import bp as auth_bp
    from app.order.routes import bp as order_bp
    from app.product.routes import bp as product_bp

    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(product_bp, url_prefix="/api/products")
    app.register_blueprint(order_bp, url_prefix="/api/orders")

    from app.commands import register_commands

    register_commands(app)

    from app.errors import register_error_handlers

    register_error_handlers(app)

    # Serve the generated OpenAPI docs once every route is registered.
    api.register(app)

    with app.app_context():
        from app import models  # noqa: F401

    return app
