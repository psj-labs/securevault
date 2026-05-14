from datetime import datetime
import bcrypt
from extensions import db   # app.py에서 생성한 SQLAlchemy 인스턴스


class User(db.Model):
    __tablename__ = "users"

    id         = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username   = db.Column(db.String(80),  unique=True, nullable=False)
    password   = db.Column(db.String(255), nullable=False)          # bcrypt 해시
    email      = db.Column(db.String(120), nullable=False)
    role       = db.Column(db.String(20),  nullable=False, default="user")  # 'admin' | 'user'
    created_at = db.Column(db.DateTime,    default=datetime.utcnow)

    # 비밀번호 헬퍼
    def set_password(self, plain: str) -> None:
        self.password = bcrypt.hashpw(
            plain.encode("utf-8"),
            bcrypt.gensalt()
        ).decode("utf-8")

    def check_password(self, plain: str) -> bool:
        return bcrypt.checkpw(
            plain.encode("utf-8"),
            self.password.encode("utf-8")
        )

    def to_dict(self) -> dict:
        return {
            "id":         self.id,
            "username":   self.username,
            "email":      self.email,
            "role":       self.role,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
