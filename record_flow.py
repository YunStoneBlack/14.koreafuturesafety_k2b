"""K2B 화면 흐름 녹화용 스크립트.

실행하면 Playwright codegen이 브라우저를 띄운다. 그 안에서:
  1. K2B 로그인 (아이디/비밀번호 직접 입력)
  2. 나의업무 > 건설재해예방전문지도기관 기술지도지원 > 재해예방기관 기술지도
  3. 현장명 검색 -> 체크 -> 상세보기 -> 모달에서 필드 몇 개 입력
  4. 사진 첨부 버튼까지 눌러보기 (실제 파일 선택은 취소해도 됨)
  5. **저장(제출) 버튼은 누르지 말 것** -- 여기까지만 하고 브라우저 창을 닫으면 됨

브라우저 창을 닫으면 data/recorded_flow.py 에 실제 셀렉터가 담긴 코드가 자동 저장된다.
그 파일을 그대로 공유해주면 됨 (로그인 아이디/비밀번호는 코드에 남지 않음 -- 입력한 값이
텍스트로 기록되므로, 저장된 파일에서 fill(...) 인자에 실제 비밀번호가 남아있으면 지우고 공유할 것).
"""

import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent
OUTPUT_FILE = PROJECT_ROOT / "data" / "recorded_flow.py"
PYTHON = PROJECT_ROOT / "venv" / "Scripts" / "python.exe"

if __name__ == "__main__":
    OUTPUT_FILE.parent.mkdir(exist_ok=True)
    subprocess.run(
        [
            str(PYTHON),
            "-m",
            "playwright",
            "codegen",
            "--target",
            "python",
            "-o",
            str(OUTPUT_FILE),
            "https://k2b.kosha.or.kr/",
        ],
        check=False,
    )
    print(f"\n녹화 결과 저장 위치: {OUTPUT_FILE}")
    print("주의: 비밀번호를 입력했다면 파일 안의 fill(...) 값에서 지우고 공유해주세요.")
