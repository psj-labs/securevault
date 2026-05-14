import os
import jwt as pyjwt
import requests
from flask import Blueprint, request, jsonify, session, redirect, current_app
from extensions import db
from models.user import User
from config import Config

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")

KEYCLOAK_REDIRECT_URI = os.environ.get("KEYCLOAK_REDIRECT_URI", "http://192.168.11.12/api/auth/keycloak/callback")


@auth_bp.route("/register", methods=["POST"])
def register():
    data = request.get_json(silent=True) or {}
    username = data.get("username", "").strip()
    password = data.get("password", "")
    email    = data.get("email", "").strip()

    if not username or not password or not email:
        return jsonify({"error": "username, password, email 은 필수입니다"}), 400
    if User.query.filter_by(username=username).first():
        return jsonify({"error": "이미 사용 중인 username 입니다"}), 409

    user = User(username=username, email=email, role="user")
    user.set_password(password)
    db.session.add(user)
    db.session.commit()
    return jsonify({"message": "회원가입 성공", "user": user.to_dict()}), 201


@auth_bp.route("/login", methods=["POST"])
def login():
    data = request.get_json(silent=True) or {}
    username = data.get("username", "").strip()
    password = data.get("password", "")

    if not username or not password:
        return jsonify({"error": "username 과 password 는 필수입니다"}), 400

    user = User.query.filter_by(username=username).first()
    if not user or not user.check_password(password):
        return jsonify({"error": "아이디 또는 비밀번호가 올바르지 않습니다"}), 401

    session["user_id"]   = user.id
    session["username"]  = user.username
    session["role"]      = user.role
    session["auth_type"] = "session"

    return jsonify({
        "message":   "로그인 성공",
        "auth_type": "session",
        "user":      user.to_dict(),
    }), 200


@auth_bp.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return jsonify({"message": "로그아웃 되었습니다."}), 200


@auth_bp.route("/keycloak/login", methods=["GET"])
def keycloak_login():
    # next 파라미터 검증 없이 세션에 저장 => Open Redirect
    next_url = request.args.get("next", "")
    session["next"] = next_url

    auth_url = (
        f"{Config.KEYCLOAK_URL}/realms/{Config.KEYCLOAK_REALM}"
        "/protocol/openid-connect/auth"
        f"?client_id={Config.KEYCLOAK_CLIENT_ID}"
        f"&redirect_uri={KEYCLOAK_REDIRECT_URI}"
        "&response_type=code"
        "&scope=openid profile email"
    )
    return redirect(auth_url)


@auth_bp.route("/keycloak/callback", methods=["GET"])
def keycloak_callback():
    code = request.args.get("code")
    if not code:
        return jsonify({"error": "Authorization code가 없습니다"}), 400

    try:
        kc_resp = requests.post(
            Config.keycloak_token_url(),
            data={
                "grant_type":    "authorization_code",
                "client_id":     Config.KEYCLOAK_CLIENT_ID,
                "client_secret": Config.KEYCLOAK_CLIENT_SECRET,
                "code":          code,
                "redirect_uri":  KEYCLOAK_REDIRECT_URI,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=10,
        )
        kc_resp.raise_for_status()
    except requests.HTTPError:
        return jsonify({"error": "토큰 발급에 실패했습니다"}), 503
    except requests.RequestException as exc:
        current_app.logger.error(f"Keycloak 요청 실패: {exc}")
        return jsonify({"error": "인증 서버에 연결할 수 없습니다"}), 503

    token_data   = kc_resp.json()
    access_token = token_data.get("access_token")

    try:
        from middleware.token_verify import _fetch_keys
        pem_key, _ = _fetch_keys()
        payload = pyjwt.decode(
            access_token,
            pem_key,
            algorithms=["RS256"],
            options={"verify_aud": False},
        )
        username = payload.get("preferred_username")
        email    = payload.get("email") or f"{username}@keycloak.local"

        user = User.query.filter_by(username=username).first()
        if not user:
            user = User(username=username, email=email, role="user")
            user.set_password(os.urandom(16).hex())
            db.session.add(user)
            db.session.commit()
    except Exception as exc:
        current_app.logger.error(f"Keycloak 콜백 유저 처리 실패: {exc}")

    # next_url 검증 없이 리다이렉트 => JWT 토큰 외부 유출 가능
    next_url = session.pop("next", "")
    if next_url:
        return redirect(f"{next_url}?token={access_token}&auth_type=keycloak")

    return redirect(
        f"http://192.168.11.12/dashboard.html"
        f"?token={access_token}&auth_type=keycloak"
    )
