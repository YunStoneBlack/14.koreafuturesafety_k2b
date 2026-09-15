"""프로젝트 설정 — app.db 경로 등.

나중에 서버(AWS)로 이식할 때는 이 경로가 완전히 달라지므로(같은 서버 안의 다른 위치,
또는 API 호출로 대체), 이 파일 하나만 고치면 되도록 분리해둔다.
"""

from __future__ import annotations

import sys
from pathlib import Path

if getattr(sys, "frozen", False):
    # exe로 빌드된 배포판(고객 PC) -- exe 옆의 data/app.db를 쓴다. 12-1 프로젝트가
    # 고객 PC에 따로 설치돼있지 않으므로, 데모용으로 미리 만들어둔 사본을 exe와 함께
    # 배포한다(packaging/build_demo_data.py로 생성, build_exe.py가 dist/ 안에 복사).
    _BASE_DIR = Path(sys.executable).resolve().parent
    REPORT_APP_DB_PATH = _BASE_DIR / "data" / "app.db"
else:
    # 로컬 개발 환경: 12-1 프로젝트가 같은 상위 폴더(클로드 코딩) 안에 있다는 가정 --
    # 실제 개발 중인 12-1 DB를 그대로 읽어서 최신 데이터로 계속 검증할 수 있게.
    _PROJECT_14_ROOT = Path(__file__).resolve().parent.parent
    REPORT_APP_DB_PATH = (
        _PROJECT_14_ROOT.parent
        / "12-1. (주)한국미래안전 보고서 작성 자동화 프로그램 hwpx버전"
        / "data"
        / "app.db"
    )

K2B_LOGIN_URL = "https://k2b.kosha.or.kr/"
