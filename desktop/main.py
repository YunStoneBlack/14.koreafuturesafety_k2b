# -*- coding: utf-8 -*-
"""앱 진입점. 실행: venv\\Scripts\\python.exe -m desktop.main"""
import sys

from PyQt6.QtWidgets import QApplication

from .main_window import MainWindow


def main() -> None:
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
