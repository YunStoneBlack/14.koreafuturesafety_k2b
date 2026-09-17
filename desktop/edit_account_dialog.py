# -*- coding: utf-8 -*-
"""등록된 K2B 계정 1개를 수정하는 모달 -- account_dialog.py의 계정 목록에서
"수정" 버튼을 누르거나 계정을 클릭하면 뜬다."""
from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog, QFormLayout, QHBoxLayout, QLineEdit, QMessageBox, QPushButton, QVBoxLayout, QWidget,
)

from core.credentials import delete_account, get_account, list_accounts, set_account
from .gui_style import field_label, section_title


class EditAccountDialog(QDialog):
    def __init__(self, staff_name: str, parent=None):
        super().__init__(parent)
        self.staff_name = staff_name
        self.setWindowTitle(f"계정 수정 — {staff_name}")
        self.resize(380, 220)
        self.setMinimumSize(320, 200)
        self.setSizeGripEnabled(True)  # 우측 하단 크기조절 그립 -- 독립적으로 크기조절 가능

        root = QVBoxLayout(self)
        root.addWidget(section_title(f"'{staff_name}' 계정 수정"))

        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)
        form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)

        self.name_input = QLineEdit(staff_name)
        form.addRow(field_label("담당요원 이름"), self.name_input)

        self.id_input = QLineEdit()
        form.addRow(field_label("K2B 아이디"), self.id_input)

        pw_row = QHBoxLayout()
        pw_row.setContentsMargins(0, 0, 0, 0)
        self.pw_input = QLineEdit()
        self.pw_input.setEchoMode(QLineEdit.EchoMode.Password)
        pw_row.addWidget(self.pw_input)
        self.pw_toggle_btn = QPushButton("👁")
        self.pw_toggle_btn.setObjectName("SecondaryButton")
        self.pw_toggle_btn.setFixedWidth(36)
        self.pw_toggle_btn.setCheckable(True)
        self.pw_toggle_btn.toggled.connect(self._toggle_password_visible)
        pw_row.addWidget(self.pw_toggle_btn)
        pw_row_widget = QWidget()
        pw_row_widget.setLayout(pw_row)
        form.addRow(field_label("K2B 비밀번호"), pw_row_widget)

        root.addLayout(form)

        creds = get_account(staff_name)
        if creds is not None:
            self.id_input.setText(creds[0])
            self.pw_input.setText(creds[1])

        save_btn = QPushButton("수정")
        save_btn.setObjectName("PrimaryButton")
        save_btn.clicked.connect(self._save)
        root.addWidget(save_btn)

    def _toggle_password_visible(self, checked: bool) -> None:
        self.pw_input.setEchoMode(
            QLineEdit.EchoMode.Normal if checked else QLineEdit.EchoMode.Password
        )

    def _save(self) -> None:
        new_name = self.name_input.text().strip()
        user_id = self.id_input.text().strip()
        password = self.pw_input.text()
        if not new_name or not user_id or not password:
            QMessageBox.warning(self, "안내", "담당요원 이름/아이디/비밀번호를 모두 입력하세요.")
            return

        renamed = new_name != self.staff_name
        if renamed and new_name in list_accounts():
            if QMessageBox.question(
                self, "확인",
                f"'{new_name}' 계정이 이미 있습니다. 덮어쓸까요?",
            ) != QMessageBox.StandardButton.Yes:
                return

        set_account(new_name, user_id, password)
        if renamed:
            delete_account(self.staff_name)
        self.accept()
