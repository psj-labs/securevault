import os


class Config:
    # Flask 기본 설정
    SECRET_KEY = os.environ.get("FLASK_SECRET_KEY", "change-me-in-production")
    DEBUG = os.environ.get("FLASK_DEBUG", "false").lower() == "true"

    # MySQL 접속 정보
    DB_HOST = os.environ.get("DB_HOST", "127.0.0.1")
    DB_PORT = int(os.environ.get("DB_PORT", 3306))
    DB_NAME = os.environ.get("DB_NAME", "pentest_db")
    DB_USER = os.environ.get("DB_USER", "pentest_user")
    DB_PASSWORD = os.environ.get("DB_PASSWORD", "pentest_pass")

    SQLALCHEMY_DATABASE_URI = (
        f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}"
        f"@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Keycloak 설정
    KEYCLOAK_URL      = os.environ.get("KEYCLOAK_URL",      "http://keycloak:8080")
    KEYCLOAK_REALM    = os.environ.get("KEYCLOAK_REALM",    "pentest-realm")
    KEYCLOAK_CLIENT_ID     = os.environ.get("KEYCLOAK_CLIENT_ID",     "pentest-client")
    KEYCLOAK_CLIENT_SECRET = os.environ.get("KEYCLOAK_CLIENT_SECRET", "super-secret")

    # Keycloak 토큰 엔드포인트
    @classmethod
    def keycloak_token_url(cls) -> str:
        return (
            f"{cls.KEYCLOAK_URL}/realms/{cls.KEYCLOAK_REALM}"
            "/protocol/openid-connect/token"
        )

    # Keycloak JWKS 엔드포인트 (공개키 조회용)
    @classmethod
    def keycloak_jwks_url(cls) -> str:
        return (
            f"{cls.KEYCLOAK_URL}/realms/{cls.KEYCLOAK_REALM}"
            "/protocol/openid-connect/certs"
        )

    # 파일 업로드 설정
    UPLOAD_FOLDER   = os.environ.get("UPLOAD_FOLDER", "/var/www/uploads")
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024   # 16 MB
