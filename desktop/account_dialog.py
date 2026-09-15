# -*- coding: utf-8 -*-
"""K2B 로그인 계정 관리 다이얼로그 — 담당요원별로 여러 계정을 등록/삭제한다.

배경: K2B "점검자" 필드가 로그인 계정 이름으로 고정되는 readonly 필드라(작업내용.md
참고), 담당요원마다 K2B 계정이 따로 있을 수 있다는 전제로 여러 계정을 이름으로 구분해
저장한다."""
from __future__ import annotations

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QListWidget, QMessageBox
)

from core.credentials import delete_account, list_accounts, set_account
from .gui_style import field_label, section_title


class AccountDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("K2B 로그인 계정 관리")
        self.resize(420, 380)

        root = QVBoxLayout(self)
        root.addWidget(section_title("등록된 계정"))

        self.account_list = QListWidget()
        root.addWidget(self.account_list)

        del_btn = QPushButton("선택 계정 삭제")
        del_btn.setObjectName("SecondaryButton")
        del_btn.clicked.connect(self._delete_selected)
        root.addWidget(del_btn)

        root.addWidget(section_title("새 계정 추가"))
        form = QHBoxLayout()
        form.addWidget(field_label("담당요원 이름"))
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("예: 현수아 (12-1 DB의 담당요원 이름과 동일하게)")
        form.addWidget(self.name_input)
        root.addLayout(form)

        form2 = QHBoxLayout()
        form2.addWidget(field_label("K2B 아이디"))
        self.id_input = QLineEdit()
        form2.addWidget(self.id_input)
        root.addLayout(form2)

        form3 = QHBoxLayout()
        form3.addWidget(field_label("K2B 비밀번호"))
        self.pw_input = QLineEdit()
        self.pw_input.setEchoMode(QLineEdit.EchoMode.Password)
        form3.addWidget(self.pw_input)
        root.addLayout(form3)

        add_btn = QPushButton("추가 / 갱신")
        add_btn.setObjectName("PrimaryButton")
        add_btn.clicked.connect(self._add_account)
        root.addWidget(add_btn)

        note = QLabel("비밀번호는 이 PC의 Windows 자격 증명 관리자에 암호화 저장됩니다.")
        note.setObjectName("FooterLabel")
        root.addWidget(note)

        self._reload_list()

    def _reload_list(self) -> None:
        self.account_list.clear()
        self.account_list.addItems(list_accounts())

    def _add_account(self) -> None:
        name = self.name_input.text().strip()
        user_id = self.id_input.text().strip()
        password = self.pw_input.text()
        if not name or not user_id or not password:
            QMessageBox.warning(self, "안내", "담당요원 이름/아이디/비밀번호를 모두 입력하세요.")
            return
        set_account(name, user_id, password)
        self.name_input.clear()
        self.id_input.clear()
        self.pw_input.clear()
        self._reload_list()

    def _delete_selected(self) -> None:
        item = self.account_list.currentItem()
        if item is None:
            return
        name = item.text()
        if QMessageBox.question(self, "확인", f"'{name}' 계정을 삭제할까요?") == QMessageBox.StandardButton.Yes:
            delete_account(name)
            self._reload_list()
