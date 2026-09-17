# -*- coding: utf-8 -*-
"""메인(랜딩) 윈도우 — K2B 로그인 계정을 고른 뒤 "신규 현장 등록"/"기존 현장에 보고서
추가 등록" 중 하나를 골라 해당 모달을 연다.

예전엔 이 창 하나에 현장/회차 선택~실행까지 전부 있었는데, 성격이 다른 두 작업(신규
현장 등록 vs 기존 현장 보고서 추가)을 한 화면에 욱여넣고 있어서 분리했다(2026-09-17,
사용자 요청). 기존 내용은 `existing_site_dialog.py`로 옮겼다."""
from __future__ import annotations

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QComboBox, QPushButton

from core.credentials import list_accounts
from .account_dialog import AccountDialog
from .existing_site_dialog import ExistingSiteDialog
from .gui_style import make_card, make_window_icon, section_title, field_label
from .new_site_dialog import NewSiteDialog


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setObjectName("Central")
        self.setWindowTitle("한국미래안전 K2B 서류 자동제출 프로그램")
        self.setWindowIcon(make_window_icon())
        # 카드 2개(계정 선택 + 작업 선택, 버튼 2개 포함)가 다 들어가려면 이 정도
        # 높이가 필요하다 -- 너무 작으면 아래쪽 버튼들이 짜부라져 텍스트가 안 보이는
        # 문제가 실사용 중 발견됨(2026-09-17).
        self.resize(520, 460)
        self.setMinimumSize(420, 420)

        # 모달을 부모 없이(독립 창으로) 띄우기 때문에, 파이썬이 참조를 잃고 바로
        # 가비지컬렉트하지 않도록 열려있는 동안 여기 붙잡아둔다.
        self._open_dialogs: list = []

        self._build_ui()
        self._reload_account_list()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 20, 24, 20)
        root.setSpacing(16)

        card, layout = make_card()
        layout.addWidget(section_title("K2B 로그인 계정"))
        account_row = QHBoxLayout()
        self.account_combo = QComboBox()
        self.account_combo.currentTextChanged.connect(self._update_action_buttons)
        account_row.addWidget(self.account_combo, stretch=1)
        manage_account_btn = QPushButton("계정 관리")
        manage_account_btn.setObjectName("SecondaryButton")
        manage_account_btn.clicked.connect(self._open_account_dialog)
        account_row.addWidget(manage_account_btn)
        layout.addLayout(account_row)
        root.addWidget(card)

        card2, layout2 = make_card()
        layout2.addWidget(section_title("작업 선택"))
        layout2.addWidget(field_label("계정을 먼저 선택한 뒤, 진행할 작업을 고르세요."))

        self.new_site_btn = QPushButton("신규 현장 등록")
        self.new_site_btn.setObjectName("SecondaryButton")
        self.new_site_btn.setMinimumHeight(40)
        self.new_site_btn.clicked.connect(self._open_new_site_dialog)
        layout2.addWidget(self.new_site_btn)

        self.existing_site_btn = QPushButton("기존 현장에 보고서 추가 등록")
        self.existing_site_btn.setObjectName("PrimaryButton")
        self.existing_site_btn.setMinimumHeight(44)
        self.existing_site_btn.clicked.connect(self._open_existing_site_dialog)
        layout2.addWidget(self.existing_site_btn)

        root.addWidget(card2)
        root.addStretch()

    # ------------------------------------------------------------ accounts

    def _reload_account_list(self, select_name: str | None = None) -> None:
        current = select_name or self.account_combo.currentText()
        self.account_combo.clear()
        self.account_combo.addItems(list_accounts())
        if current:
            idx = self.account_combo.findText(current)
            if idx >= 0:
                self.account_combo.setCurrentIndex(idx)
        self._update_action_buttons()

    def _open_account_dialog(self) -> None:
        # 부모를 안 붙이고 setModal(False) -- 메인 창을 계속 독립적으로 옮기거나
        # 조작할 수 있게 한다(예전엔 exec()로 띄워서 메인 창이 멈춰있었음).
        dialog = AccountDialog()
        dialog.setModal(False)
        dialog.finished.connect(lambda *_: self._reload_account_list())
        self._open_dialogs.append(dialog)
        dialog.show()

    def _update_action_buttons(self, *_args) -> None:
        has_account = bool(self.account_combo.currentText().strip())
        self.new_site_btn.setEnabled(has_account)
        self.existing_site_btn.setEnabled(has_account)

    # -------------------------------------------------------------- modals

    def _open_new_site_dialog(self) -> None:
        dialog = NewSiteDialog()
        dialog.setModal(False)
        self._open_dialogs.append(dialog)
        dialog.show()

    def _open_existing_site_dialog(self) -> None:
        account_name = self.account_combo.currentText().strip()
        dialog = ExistingSiteDialog(account_name)
        dialog.setModal(False)
        self._open_dialogs.append(dialog)
        dialog.show()
