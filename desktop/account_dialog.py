# -*- coding: utf-8 -*-
"""K2B 로그인 계정 관리 다이얼로그 — 담당요원별로 여러 계정을 등록/삭제한다.

배경: K2B "점검자" 필드가 로그인 계정 이름으로 고정되는 readonly 필드라(작업내용.md
참고), 담당요원마다 K2B 계정이 따로 있을 수 있다는 전제로 여러 계정을 이름으로 구분해
저장한다."""
from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QLabel, QLineEdit, QPushButton,
    QListWidget, QMessageBox, QWidget,
)

from core.credentials import delete_account, list_accounts, set_account
from .edit_account_dialog import EditAccountDialog
from .gui_style import field_label, section_title


class AccountDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("K2B 로그인 계정 관리")
        self.resize(420, 520)
        self.setMinimumSize(360, 400)
        self.setSizeGripEnabled(True)  # 우측 하단 크기조절 그립 -- 독립적으로 크기조절 가능
        self._open_dialogs: list = []  # 수정 모달을 비모달로 띄울 때 참조 유지용

        root = QVBoxLayout(self)
        root.addWidget(section_title("등록된 계정"))

        self.account_list = QListWidget()
        # 기본 sizeHint대로면 2~3줄밖에 안 보여서 6줄 정도 보이게 최소 높이를 지정한다.
        # QListWidget은 기본적으로 스크롤 영역이라, 10개가 등록돼도 이 높이를 넘는 부분은
        # 자동으로 세로 스크롤바가 생겨 스크롤해서 볼 수 있다(별도 구현 불필요).
        self.account_list.setMinimumHeight(190)
        root.addWidget(self.account_list)

        list_btn_row = QHBoxLayout()
        edit_btn = QPushButton("선택 계정 수정")
        edit_btn.setObjectName("SecondaryButton")
        edit_btn.clicked.connect(self._edit_selected)
        list_btn_row.addWidget(edit_btn, stretch=1)
        del_btn = QPushButton("선택 계정 삭제")
        del_btn.setObjectName("SecondaryButton")
        del_btn.clicked.connect(self._delete_selected)
        list_btn_row.addWidget(del_btn, stretch=1)
        root.addLayout(list_btn_row)

        root.addWidget(section_title("새 계정 추가"))
        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)
        form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("예: 현수아 (12-1 DB의 담당요원 이름과 동일하게)")
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

    def _toggle_password_visible(self, checked: bool) -> None:
        self.pw_input.setEchoMode(
            QLineEdit.EchoMode.Normal if checked else QLineEdit.EchoMode.Password
        )

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

    def _edit_selected(self) -> None:
        item = self.account_list.currentItem()
        if item is None:
            QMessageBox.information(self, "안내", "수정할 계정을 목록에서 먼저 선택하세요.")
            return
        self._open_edit_dialog(item.text())

    def _open_edit_dialog(self, name: str) -> None:
        # 부모 없이 setModal(False)로 띄워서 이 계정 관리 창도 독립적으로 옮기거나
        # 조작할 수 있게 한다.
        dialog = EditAccountDialog(name)
        dialog.setModal(False)
        dialog.finished.connect(lambda *_: self._reload_list())
        self._open_dialogs.append(dialog)
        dialog.show()

    def _delete_selected(self) -> None:
        item = self.account_list.currentItem()
        if item is None:
            return
        name = item.text()
        if QMessageBox.question(self, "확인", f"'{name}' 계정을 삭제할까요?") == QMessageBox.StandardButton.Yes:
            delete_account(name)
            self._reload_list()
