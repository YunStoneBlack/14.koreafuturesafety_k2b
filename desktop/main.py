# -*- coding: utf-8 -*-
"""앱 진입점. 실행: venv\\Scripts\\python.exe -m desktop.main

절대 임포트(`from desktop...`)를 쓴다 -- PyInstaller로 빌드된 exe는 이 파일을 패키지의
일부가 아니라 최상위 스크립트로 실행하기 때문에 상대 임포트(`from .main_window`)가
"attempted relative import with no known parent package"로 실패한다(실제 빌드 후
재현해서 확인함). 절대 임포트는 `-m desktop.main`으로 돌리는 개발 환경에서도 그대로
동작하므로 양쪽 다 이 방식으로 통일한다."""
import sys

from PyQt6.QtWidgets import QApplication

from desktop.gui_style import build_style_sheet
from desktop.main_window import MainWindow


def main() -> None:
    app = QApplication(sys.argv)
    # 앱(QApplication) 레벨로 스타일시트를 적용한다 -- 위젯 레벨(MainWindow 등)에만
    # 걸면 그 위젯의 자식(parent-child)에만 상속되는데, 계정관리/신규현장/기존현장 모달을
    # "메인 창을 독립적으로 옮길 수 있게" 부모 없이(parent=None) 띄우도록 바꾸면서
    # (2026-09-17) 그 모달들이 스타일을 하나도 못 받는 문제가 생겼음(실사용 중 발견).
    # 앱 전체에 적용하면 부모 유무와 무관하게 모든 창에 일관되게 먹는다.
    app.setStyleSheet(build_style_sheet())
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
