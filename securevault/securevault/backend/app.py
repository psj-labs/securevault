import os
from flask import Flask
from flask_cors import CORS
from dotenv import load_dotenv

# .env 파일이 있으면 자동 로드
load_dotenv()

from config import Config
from extensions import db


def create_app(config_class=Config) -> Flask:
    app = Flask(__name__)
    app.config.from_object(config_class)

    # 확장 초기화
    db.init_app(app)
    CORS(app, origins=["http://192.168.11.12"], supports_credentials=True)

    # Blueprint 등록
    from routes.auth    import auth_bp
    from routes.users   import users_bp
    from routes.notices import notices_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(users_bp)
    app.register_blueprint(notices_bp)

    # DB 테이블 자동 생성
    with app.app_context():
        db.create_all()

    # 업로드 디렉터리 생성
    upload_dir = app.config.get("UPLOAD_FOLDER", "/var/www/uploads")
    os.makedirs(upload_dir, exist_ok=True)

    # CORS 헤더 (Apache 프록시 사용 시 불필요할 수 있음)
    @app.after_request
    def add_cors_headers(response):
        response.headers["Access-Control-Allow-Origin"]  = "http://192.168.11.12"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
        response.headers["Access-Control-Allow-Credentials"] = "true"
        return response

    @app.route("/health")
    def health():
        return {"status": "ok"}, 200

    return app


if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=5000, debug=Config.DEBUG)
