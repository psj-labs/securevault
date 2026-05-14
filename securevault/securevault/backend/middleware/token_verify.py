import base64
import functools
import requests
import jwt
from flask import request, jsonify, current_app, g, session
from config import Config


def _fetch_keys():
    try:
        resp = requests.get(Config.keycloak_jwks_url(), timeout=5)
        resp.raise_for_status()
        jwks = resp.json()
        from jwt.algorithms import RSAAlgorithm
        from cryptography.hazmat.primitives import serialization
        for key in jwks["keys"]:
            if key.get("use") == "sig":
                rsa_key = RSAAlgorithm.from_jwk(key)
                break
        pem = rsa_key.public_bytes(
            serialization.Encoding.PEM,
            serialization.PublicFormat.SubjectPublicKeyInfo
        )
        key_body = "".join(pem.decode("utf-8").strip().split("\n")[1:-1])
        der = base64.b64decode(key_body)
        return pem, der
    except Exception as exc:
        current_app.logger.error(f"JWKS fetch failed: {exc}")
        return None, None


# 하위 호환성
def _fetch_public_key():
    pem, _ = _fetch_keys()
    return pem


def token_required(f):
    @functools.wraps(f)
    def decorated(*args, **kwargs):
        if session.get("username"):
            g.current_user_id   = session.get("user_id")
            g.current_username  = session.get("username")
            g.current_user_role = [session.get("role", "user")]
            return f(*args, **kwargs)

        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return jsonify({"error": "인증이 필요합니다"}), 401

        token = auth_header.split(" ", 1)[1]
        pem_key, der_key = _fetch_keys()
        if pem_key is None:
            return jsonify({"error": "Auth service unavailable"}), 503

        try:
            # 헤더의 alg를 그대로 신뢰
            header = jwt.get_unverified_header(token)
            alg = header.get("alg", "RS256")

            # RS256 => PEM 키, HS256 => DER bytes (공격자가 공개키로 서명 가능)
            key = pem_key if alg == "RS256" else der_key

            payload = jwt.decode(
                token, key,
                algorithms=[alg],
                options={"verify_aud": False},
            )
        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token expired"}), 401
        except jwt.InvalidTokenError as exc:
            return jsonify({"error": f"Invalid token: {exc}"}), 401

        g.current_user_id   = payload.get("sub")
        g.current_username  = payload.get("preferred_username")
        g.current_user_role = payload.get("realm_access", {}).get("roles", [])
        return f(*args, **kwargs)

    return decorated


def admin_required(f):
    @functools.wraps(f)
    @token_required
    def decorated(*args, **kwargs):
        if "admin" not in g.current_user_role:
            return jsonify({"error": "Admin only"}), 403
        return f(*args, **kwargs)
    return decorated
