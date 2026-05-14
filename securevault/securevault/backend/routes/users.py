from flask import Blueprint, request, jsonify, g
from extensions import db
from models.user import User
from middleware.token_verify import token_required

users_bp = Blueprint("users", __name__, url_prefix="/api/users")


# 내 정보 조회
@users_bp.route("/me", methods=["GET"])
@token_required
def get_me():
    user = User.query.filter_by(username=g.current_username).first()
    if not user:
        return jsonify({
            "id": g.current_user_id,
            "username": g.current_username,
            "email": "",
            "role": g.current_user_role[0] if g.current_user_role else "user",
            "created_at": None,
        }), 200
    return jsonify(user.to_dict()), 200

# 내 정보 수정
@users_bp.route("/me", methods=["PUT"])
@token_required
def update_me():
    user = User.query.filter_by(username=g.current_username).first()
    if not user:
        return jsonify({"error": "유저를 찾을 수 없습니다"}), 404

    data = request.get_json(silent=True) or {}

    if "email" in data:
        user.email = data["email"]

    if "password" in data and data["password"]:
        current_password = data.get("current_password", "")
        new_password     = data.get("password", "")
        confirm_password = data.get("confirm_password", "")

        if not user.check_password(current_password):
            return jsonify({"error": "현재 비밀번호가 올바르지 않습니다"}), 400

        if len(new_password) < 8:
            return jsonify({"error": "비밀번호는 8자 이상이어야 합니다"}), 400

        if new_password != confirm_password:
            return jsonify({"error": "새 비밀번호가 일치하지 않습니다"}), 400

        user.set_password(new_password)

    db.session.commit()
    return jsonify({"message": "수정 완료", "user": user.to_dict()}), 200
