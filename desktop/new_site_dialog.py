# -*- coding: utf-8 -*-
"""신규 현장(K2B에 한 번도 등록된 적 없는 현장) 등록 모달 -- 껍데기.

실제 K2B "신규 등록" 화면 구조를 아직 몰라서(고객 미팅 후 확정 예정, 작업내용.md/
프로젝트 메모리의 TODO 참고) 내용은 못 채웠고, 나중에 이 파일 안에 폼/자동화를 채워
넣을 자리만 미리 마련해둔다."""
from __future__ import annotations

from PyQt6.QtWidgets import QDialog, QLabel, QVBoxLayout

from .gui_style import section_title


class NewSiteDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("신규 현장 등록")
        self.resize(480, 260)
        self.setMinimumSize(360, 200)
        self.setSizeGripEnabled(True)  # 우측 하단 크기조절 그립 -- 독립적으로 크기조절 가능

        root = QVBoxLayout(self)
        root.addWidget(section_title("신규 현장 등록"))

        note = QLabel(
            "아직 준비 중인 기능입니다.\n\n"
            "K2B에 한 번도 등록된 적 없는 현장(1회차)을 처음부터 등록하는 화면이 여기 "
            "들어갈 예정입니다 -- 실제 K2B 신규 등록 화면 구조를 확인한 뒤 구현합니다."
        )
        note.setWordWrap(True)
        root.addWidget(note)
        root.addStretch()
