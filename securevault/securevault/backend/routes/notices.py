import os
import pathlib
from datetime import datetime
from flask import Blueprint, request, jsonify, current_app, g
from extensions import db
from models.user import User
from models.notice import Notice
from middleware.token_verify import token_required

notices_bp = Blueprint("notices", __name__, url_prefix="/api/notices")

BLOCKED_EXTENSIONS = frozenset({
    ".php", ".py", ".sh", ".bash", ".rb", ".pl",
    ".cgi", ".jsp", ".asp", ".aspx", ".exe", ".bat", ".cmd", ".ps1",
})


def _is_admin() -> bool:
    user = User.query.filter_by(username=g.current_username).first()
    return user is not None and user.role == "admin"


def _check_file(filename: str, content_type: str):
    """
      두 가지 취약점이 존재한다.
      1. 블랙리스트 방식 — .php5, .phtml, .phar 등은 검증을 통과함
      2. Content-Type 을 클라이언트 제공 값으로 신뢰 — 위변조 가능
    """
    ext = pathlib.Path(filename).suffix.lower()

    if ext in BLOCKED_EXTENSIONS:
        return f"허용되지 않는 파일 형식입니다: {ext}"

    # Content-Type 을 클라이언트 헤더 값 그대로 신뢰
    #              curl -F "file=@shell.php5;type=image/jpeg" 로 우회 가능
    dangerous_mime = {"application/x-php", "text/x-php", "application/x-sh"}
    if content_type in dangerous_mime:
        return "허용되지 않는 Content-Type 입니다."

    return None  


# 공지사항 목록 조회
@notices_bp.route("", methods=["GET"])
@token_required
def list_notices():
    """GET /api/notices  –  최신순 공지사항 목록 반환 (인증 유저 전체)."""
    notices = Notice.query.order_by(Notice.created_at.desc()).all()
    return jsonify([n.to_dict() for n in notices]), 200


# 공지사항 단건 조회
@notices_bp.route("/<int:notice_id>", methods=["GET"])
@token_required
def get_notice(notice_id):
    """GET /api/notices/<id>  –  단건 조회 (인증 유저 전체)."""
    notice = Notice.query.get(notice_id)
    if not notice:
        return jsonify({"error": "공지사항을 찾을 수 없습니다."}), 404
    return jsonify(notice.to_dict()), 200


# 공지사항 등록
@notices_bp.route("", methods=["POST"])
@token_required
def create_notice():
    """
    POST /api/notices  –  공지 등록 (admin 전용).

    multipart/form-data:
      title   (string, 필수)
      content (string, 필수)
      file    (file,   선택)
    """
    if not _is_admin():
        return jsonify({"error": "관리자만 공지사항을 등록할 수 있습니다."}), 403

    title   = request.form.get("title",   "").strip()
    content = request.form.get("content", "").strip()

    if not title or not content:
        return jsonify({"error": "title 과 content 는 필수입니다."}), 400

    author = User.query.filter_by(username=g.current_username).first()

    saved_filename = None

    # 파일 첨부 처리
    if "file" in request.files:
        file = request.files["file"]

        if file.filename and file.filename != "":
            err = _check_file(file.filename, file.content_type)
            if err:
                return jsonify({"error": err}), 400

            upload_dir = current_app.config["UPLOAD_FOLDER"]
            os.makedirs(upload_dir, exist_ok=True)

            # 원본 파일명 그대로 사용 (Path Traversal 가능성)
            saved_filename = file.filename
            file.save(os.path.join(upload_dir, saved_filename))

    notice = Notice(
        title      = title,
        content    = content,
        author_id  = author.id,
        filename   = saved_filename,
        file_path  = os.path.join(current_app.config["UPLOAD_FOLDER"], saved_filename)
                     if saved_filename else None,
    )
    db.session.add(notice)
    db.session.commit()

    return jsonify({"message": "공지사항이 등록되었습니다.", "notice": notice.to_dict()}), 201
