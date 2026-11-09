from flask_jwt_extended import JWTManager
from flask_sqlalchemy import SQLAlchemy
from spectree import SecurityScheme, SpecTree
from spectree.models import SecureType, SecuritySchemeData

db = SQLAlchemy()
jwt = JWTManager()

# OpenAPI generator. It only produces the docs: every route keeps its own
# Pydantic validation and error handling, so endpoints are decorated with
# skip_validation=True and Spectree never intercepts a request.
api = SpecTree(
    "flask",
    title="DigiMarket API",
    version="1.0.0",
    path="api/docs",
    # Our routes return 400 (not Spectree's default 422) on a bad body, so the
    # documented validation-error code matches what clients actually get.
    validation_error_status=400,
    # Protected routes expect a JWT bearer token; this drives Swagger's Authorize.
    security_schemes=[
        SecurityScheme(
            name="bearerAuth",
            data=SecuritySchemeData(
                type=SecureType.HTTP, scheme="bearer", bearer_format="JWT"
            ),
        )
    ],
)

# OpenAPI security requirement referencing the scheme above, for protected routes.
BEARER = [{"bearerAuth": []}]


@jwt.user_lookup_loader
def load_user(_, jwt_data):
    from app.models import User

    return db.session.get(User, int(jwt_data["sub"]))
