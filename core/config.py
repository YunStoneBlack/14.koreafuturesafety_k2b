"""프로젝트 설정 — 12-1 프로젝트 app.db 경로 등.

나중에 서버(AWS)로 이식할 때는 이 경로가 완전히 달라지므로(같은 서버 안의 다른 위치,
또는 API 호출로 대체), 이 파일 하나만 고치면 되도록 분리해둔다.
"""

from __future__ import annotations

from pathlib import Path

# 로컬 개발 환경: 12-1 프로젝트가 같은 상위 폴더(클로드 코딩) 안에 있다는 가정.
_PROJECT_14_ROOT = Path(__file__).resolve().parent.parent
REPORT_APP_DB_PATH = (
    _PROJECT_14_ROOT.parent
    / "12-1. (주)한국미래안전 보고서 작성 자동화 프로그램 hwpx버전"
    / "data"
    / "app.db"
)

K2B_LOGIN_URL = "https://k2b.kosha.or.kr/"
