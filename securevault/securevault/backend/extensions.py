"""
extensions.py
-------------
Flask 확장 인스턴스를 한 곳에서 선언해 순환 임포트를 방지한다.
app.py에서 init_app()으로 초기화한다.
"""

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
