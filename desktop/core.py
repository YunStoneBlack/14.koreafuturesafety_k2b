# -*- coding: utf-8 -*-
"""데스크톱 앱 전역 경로. 6/7/8/10/11번 프로젝트와 같은 패턴 —
exe로 빌드(PyInstaller)되면 sys.executable 옆, 소스 실행 중이면 프로젝트 루트."""
import sys
from pathlib import Path

if getattr(sys, "frozen", False):
    PROJECT_ROOT = Path(sys.executable).resolve().parent
else:
    PROJECT_ROOT = Path(__file__).resolve().parent.parent
