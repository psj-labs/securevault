from datetime import datetime
from extensions import db


class Notice(db.Model):
    __tablename__ = "notices"

    id           = db.Column(db.Integer,  primary_key=True, autoincrement=True)
    title        = db.Column(db.String(200), nullable=False)
    content      = db.Column(db.Text,        nullable=False)
    author_id    = db.Column(db.Integer,  db.ForeignKey("users.id"), nullable=False)
    filename     = db.Column(db.String(255), nullable=True)   # 첨부파일 원본명
    file_path    = db.Column(db.String(512), nullable=True)   # 서버 저장 경로
    created_at   = db.Column(db.DateTime, default=datetime.utcnow)

    author = db.relationship("User", backref="notices", lazy="joined")

    def to_dict(self) -> dict:
        return {
            "id":         self.id,
            "title":      self.title,
            "content":    self.content,
            "author":     self.author.username if self.author else None,
            "filename":   self.filename,
            "file_url":   f"/uploads/{self.filename}" if self.filename else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
