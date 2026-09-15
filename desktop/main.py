# -*- coding: utf-8 -*-
"""앱 진입점. 실행: venv\\Scripts\\python.exe -m desktop.main

절대 임포트(`from desktop...`)를 쓴다 -- PyInstaller로 빌드된 exe는 이 파일을 패키지의
일부가 아니라 최상위 스크립트로 실행하기 때문에 상대 임포트(`from .main_window`)가
"attempted relative import with no known parent package"로 실패한다(실제 빌드 후
재현해서 확인함). 절대 임포트는 `-m desktop.main`으로 돌리는 개발 환경에서도 그대로
동작하므로 양쪽 다 이 방식으로 통일한다."""
import sys

from PyQt6.QtWidgets import QApplication

from desktop.main_window import MainWindow


def main() -> None:
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
