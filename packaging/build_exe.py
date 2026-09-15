"""고객 배포용 exe를 빌드한다 (12-1 프로젝트의 packaging/build_exe.py 패턴 참고).

Playwright는 이 앱 자체가 설치한 Chromium을 쓰지 않고 **고객 PC에 이미 설치된 구글
크롬**을 그대로 제어한다(core/k2b_client.py의 `open_browser()` 참고) — 그래서 Chromium
바이너리(150MB+)를 통째로 배포판에 넣을 필요가 없다. 대신 고객 PC에 크롬이 설치돼
있어야 하고, 없으면 실행 시 안내 메시지가 뜬다.

데이터베이스(`data/demo/app.db`)는 12-1의 실제 테스트 데이터를 이 PC 절대경로 의존 없이
복사해둔 사본이다(`packaging/build_demo_data.py`로 미리 생성 — 이 스크립트보다 먼저
실행해야 함). 그래서 고객이 exe만 받아도 "불러오기"가 바로 동작해 실제 화면을 볼 수 있다.

실행 순서:
    python packaging/build_demo_data.py   # 최초 1회 또는 데모 데이터 갱신 시
    python packaging/build_exe.py

결과: 바탕화면\한국미래안전_K2B자동제출\ 폴더에 exe + data/ 준비 완료. 이 폴더 전체를
고객에게 전달(압축해서 보내거나 USB로 복사)하면 된다.
"""

from __future__ import annotations

import os
import shutil
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
APP_NAME = "한국미래안전_K2B자동제출"

# 배포 폴더는 바탕화면에 만든다(사용자 요청) -- 바로 찾아서 압축/전달하기 쉽게.
DESKTOP = Path(os.environ.get("USERPROFILE", str(Path.home()))) / "Desktop"
DIST_DIR = DESKTOP


def _run_pyinstaller() -> None:
    from PyInstaller.__main__ import run as pyinstaller_run

    args = [
        str(PROJECT_ROOT / "desktop" / "main.py"),
        "--name", APP_NAME,
        "--onedir",
        "--windowed",
        "--noconfirm",
        "--paths", str(PROJECT_ROOT),
        # 이 개발 PC에 PyQt5/PySide도 같이 깔려있을 수 있어(다른 프로젝트용) PyInstaller가
        # "Qt 바인딩 두 개를 동시에 못 묶는다"며 중단시킬 수 있다 -- 이 앱은 PyQt6만
        # 쓰므로 명시적으로 제외한다(12-1 프로젝트에서도 같은 이유로 제외).
        "--exclude-module", "PyQt5",
        "--exclude-module", "PySide2",
        "--exclude-module", "PySide6",
        "--distpath", str(DIST_DIR),
        "--workpath", str(PROJECT_ROOT / "build"),
        "--specpath", str(PROJECT_ROOT / "packaging"),
    ]
    pyinstaller_run(args)


def _copy_runtime_data(dist_dir: Path) -> None:
    demo_src = PROJECT_ROOT / "data" / "demo"
    if not demo_src.exists():
        raise SystemExit(
            "data/demo/가 없습니다. 먼저 실행하세요: python packaging/build_demo_data.py"
        )
    data_dest = dist_dir / "data"
    data_dest.mkdir(parents=True, exist_ok=True)
    for item in demo_src.iterdir():
        dest = data_dest / item.name
        if item.is_dir():
            shutil.copytree(item, dest, dirs_exist_ok=True)
        else:
            shutil.copy2(item, dest)


def main() -> None:
    _run_pyinstaller()
    dist_dir = DIST_DIR / APP_NAME
    _copy_runtime_data(dist_dir)
    print(f"\n완료: {dist_dir} 폴더 전체를 고객에게 전달하면 됩니다.")
    print("주의: 고객 PC에 구글 크롬이 설치되어 있어야 합니다(Playwright가 그 크롬을 제어함).")


if __name__ == "__main__":
    main()
