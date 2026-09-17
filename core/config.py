"""프로젝트 설정 — app.db 경로 등.

나중에 서버(AWS)로 이식할 때는 이 경로가 완전히 달라지므로(같은 서버 안의 다른 위치,
또는 API 호출로 대체), 이 파일 하나만 고치면 되도록 분리해둔다.
"""

from __future__ import annotations

import sys
from pathlib import Path

if getattr(sys, "frozen", False):
    # exe로 빌드된 배포판(담당요원 PC) -- 실배포 방식은 "12-1(보고서 작성)/14(K2B제출)
    # 두 exe를 같은 상위 폴더 밑에 나란히 설치"하는 것으로 확정함(2026-09-17). 그래서
    # 14 exe 폴더의 부모 밑에서 12-1의 dist 폴더 이름(12-1 packaging/build_exe.py의
    # APP_NAME과 반드시 일치해야 함)을 찾아 그 실제 app.db를 쓴다 -- 담당요원이 12-1로
    # 작성한 보고서가 실시간으로 14에 반영되게 하려면 이 방식이어야 한다(exe에 고정
    # 번들한 데모 DB로는 안 됨).
    # 12-1이 옆에 없는 경우(순수 데모 배포, 영업용 등)에는 예전처럼 exe에 같이 번들해둔
    # 데모 사본(packaging/build_demo_data.py로 생성)으로 대체한다.
    _REPORT_APP_DIST_NAME = "한국미래안전_기술지도결과보고서"
    _BASE_DIR = Path(sys.executable).resolve().parent
    _sibling_db = _BASE_DIR.parent / _REPORT_APP_DIST_NAME / "data" / "app.db"
    REPORT_APP_DB_PATH = _sibling_db if _sibling_db.exists() else _BASE_DIR / "data" / "app.db"
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
