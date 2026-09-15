"""고객 데모/배포용 app.db 사본을 만든다.

12-1 프로젝트의 실제 app.db는 파일 경로를 이 개발 PC의 절대경로로 저장하고 있어서
(예: "C:\\Users\\...\\report_6.pdf") 그대로 exe와 함께 배포하면 고객 PC에서 경로가
깨진다. 이 스크립트는:
  1. 12-1의 app.db를 이 프로젝트의 data/demo/app.db로 복사
  2. 그 DB가 가리키는 보고서 PDF 파일 실물도 data/demo/ 밑에 같이 복사
  3. DB 안의 pdf_path를 **파일명만 남긴 상대경로**로 바꿔써서, db_reader.py가
     "DB 파일이 있는 폴더 기준"으로 다시 찾을 수 있게 한다(core/db_reader.py의
     `_resolve_path()` 참고) — 그래서 이 data/demo/ 폴더를 통째로 어디로 옮겨도
     (배포 exe 옆이든 어디든) 안 깨진다.

실행: python packaging/build_demo_data.py
결과: data/demo/app.db, data/demo/<보고서파일>.pdf
"""

from __future__ import annotations

import shutil
import sqlite3
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SOURCE_DB = (
    PROJECT_ROOT.parent
    / "12-1. (주)한국미래안전 보고서 작성 자동화 프로그램 hwpx버전"
    / "data"
    / "app.db"
)
DEMO_DIR = PROJECT_ROOT / "data" / "demo"


def main() -> None:
    if not SOURCE_DB.exists():
        raise SystemExit(f"원본 DB를 찾을 수 없습니다: {SOURCE_DB}")

    DEMO_DIR.mkdir(parents=True, exist_ok=True)
    demo_db = DEMO_DIR / "app.db"
    shutil.copy2(SOURCE_DB, demo_db)

    conn = sqlite3.connect(demo_db)
    conn.row_factory = sqlite3.Row
    try:
        reports = conn.execute("SELECT id, pdf_path FROM report WHERE pdf_path != ''").fetchall()
        for row in reports:
            src_pdf = Path(row["pdf_path"])
            if not src_pdf.exists():
                print(f"경고: report {row['id']}의 PDF를 찾을 수 없어 건너뜀: {src_pdf}")
                continue
            dest_name = f"report_{row['id']}.pdf"
            shutil.copy2(src_pdf, DEMO_DIR / dest_name)
            conn.execute("UPDATE report SET pdf_path = ? WHERE id = ?", (dest_name, row["id"]))
            print(f"report {row['id']}: {src_pdf.name} -> data/demo/{dest_name}")
        # hwpx_path는 K2B가 어차피 안 받는 형식이라(core/db_reader.py 참고) 배포판에
        # 원본 그대로 두면 깨진 절대경로만 남으므로 비워서 혼동을 막는다.
        conn.execute("UPDATE report SET hwpx_path = ''")
        conn.commit()
    finally:
        conn.close()

    print(f"\n완료: {DEMO_DIR}")


if __name__ == "__main__":
    main()
