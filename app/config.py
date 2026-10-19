class DefaultConfig:
    SQLALCHEMY_DATABASE_URI = "sqlite:///app.db"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JWT_SECRET_KEY = "change-me-in-prod"  # surchargé par l'env en vrai
