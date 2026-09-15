# -*- coding: utf-8 -*-
"""메인 윈도우 — 현장/회차 선택 -> 12-1 DB에서 데이터 로드 -> K2B 자동입력 실행."""
from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTextEdit, QComboBox, QCheckBox, QMessageBox
)

from core.config import REPORT_APP_DB_PATH
from core.credentials import get_account, list_accounts
from core.db_reader import K2BSubmissionData, get_submission_data, list_rounds, list_sites
from .account_dialog import AccountDialog
from .gui_style import build_style_sheet, make_card, make_window_icon, section_title, field_label
from .worker import K2BFillWorker


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setObjectName("Central")
        self.setWindowTitle("한국미래안전 K2B 서류 자동제출 프로그램")
        self.setWindowIcon(make_window_icon())
        self.resize(880, 780)
        self.setStyleSheet(build_style_sheet())

        self._current_data: K2BSubmissionData | None = None
        self._worker: K2BFillWorker | None = None

        self._build_ui()
        self._reload_site_list()
        self._reload_account_list()

    # ------------------------------------------------------------------ UI

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(24, 20, 24, 20)
        root.setSpacing(16)

        account_row = QHBoxLayout()
        account_row.addWidget(field_label("K2B 로그인 계정"))
        self.account_combo = QComboBox()
        account_row.addWidget(self.account_combo, stretch=1)
        manage_account_btn = QPushButton("계정 관리")
        manage_account_btn.setObjectName("SecondaryButton")
        manage_account_btn.clicked.connect(self._open_account_dialog)
        account_row.addWidget(manage_account_btn)
        root.addLayout(account_row)

        card1, l1 = make_card()
        l1.addWidget(section_title("제출 대상 선택 (12-1 DB)"))
        row = QHBoxLayout()
        row.addWidget(field_label("현장명"))
        self.site_combo = QComboBox()
        self.site_combo.setEditable(True)
        self.site_combo.currentTextChanged.connect(self._reload_round_list)
        row.addWidget(self.site_combo, stretch=2)
        row.addWidget(field_label("회차"))
        self.round_combo = QComboBox()
        row.addWidget(self.round_combo, stretch=1)
        load_btn = QPushButton("불러오기")
        load_btn.setObjectName("SecondaryButton")
        load_btn.clicked.connect(self._load_data)
        row.addWidget(load_btn)
        l1.addLayout(row)
        root.addWidget(card1)

        card2, l2 = make_card()
        l2.addWidget(section_title("K2B에 입력될 내용 미리보기"))
        self.preview = QTextEdit()
        self.preview.setReadOnly(True)
        self.preview.setFixedHeight(220)
        l2.addWidget(self.preview)
        root.addWidget(card2)

        card3, l3 = make_card()
        l3.addWidget(section_title("실행 로그"))
        self.log_area = QTextEdit()
        self.log_area.setObjectName("LogArea")
        self.log_area.setReadOnly(True)
        self.log_area.setFixedHeight(160)
        l3.addWidget(self.log_area)
        root.addWidget(card3)

        action_row = QHBoxLayout()
        self.new_round_check = QCheckBox("새 차수로 추가 (K2B에 이 회차가 아직 없음)")
        self.new_round_check.setChecked(True)  # 기본값 체크 -- 꺼두면 K2B에 현재 열려있는
        # 기존 차수를 그대로 덮어쓰게 되는데, 12-1의 회차 번호와 K2B의 차수 번호는 서로
        # 무관한 별개 카운터라 실수로 엉뚱한 기존 데이터를 덮어쓸 위험이 있다(실사용 중
        # 발견). 게다가 기존 차수는 "보고서 수정가능 기한"(기술지도일+7일)이 이미 지나
        # 있을 수 있어 파일첨부 자체가 막힌다. 새 차수는 기술지도일이 오늘로 자동
        # 설정되어 이 문제가 없다 -- 기존 차수를 의도적으로 고칠 때만 체크 해제할 것.
        action_row.addWidget(self.new_round_check)
        action_row.addStretch()
        self.run_btn = QPushButton("K2B 화면에 자동 입력하기")
        self.run_btn.setObjectName("PrimaryButton")
        self.run_btn.clicked.connect(self._run_automation)
        action_row.addWidget(self.run_btn)
        root.addLayout(action_row)

        footer = QLabel("이 프로그램은 최종 저장(제출) 버튼을 자동으로 누르지 않습니다 — "
                         "화면을 확인한 뒤 직접 클릭하세요.")
        footer.setObjectName("FooterLabel")
        footer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        root.addWidget(footer)

    # ------------------------------------------------------------ accounts

    def _reload_account_list(self, select_name: str | None = None) -> None:
        current = select_name or self.account_combo.currentText()
        self.account_combo.clear()
        self.account_combo.addItems(list_accounts())
        if current:
            idx = self.account_combo.findText(current)
            if idx >= 0:
                self.account_combo.setCurrentIndex(idx)

    def _open_account_dialog(self) -> None:
        dialog = AccountDialog(self)
        dialog.exec()
        self._reload_account_list()

    # --------------------------------------------------------------- data

    def _reload_site_list(self) -> None:
        try:
            sites = list_sites(REPORT_APP_DB_PATH)
        except Exception as e:
            self._log(f"현장 목록 로드 실패: {e}")
            sites = []
        self.site_combo.clear()
        self.site_combo.addItems(sites)

    def _reload_round_list(self) -> None:
        site_name = self.site_combo.currentText().strip()
        self.round_combo.clear()
        if not site_name:
            return
        try:
            rounds = list_rounds(REPORT_APP_DB_PATH, site_name)
        except Exception as e:
            self._log(f"회차 목록 로드 실패: {e}")
            return
        for r in rounds:
            self.round_combo.addItem(f"{r}회차", userData=r)

    def _load_data(self) -> None:
        site_name = self.site_combo.currentText().strip()
        if not site_name:
            QMessageBox.warning(self, "안내", "현장명을 입력하거나 선택하세요.")
            return
        visit_no = self.round_combo.currentData()
        data = get_submission_data(REPORT_APP_DB_PATH, site_name, visit_no)
        if data is None:
            QMessageBox.warning(self, "안내", "해당 현장/회차 데이터를 찾을 수 없습니다.")
            return
        self._current_data = data
        self.preview.setPlainText(self._format_preview(data))
        self._log(f"'{site_name}' {data.visit_no}회차 데이터 로드 완료.")

        if data.inspector_name and data.inspector_name in list_accounts():
            self._reload_account_list(select_name=data.inspector_name)
            self._log(f"점검자 '{data.inspector_name}'와 이름이 같은 로그인 계정을 자동 선택했습니다.")
        elif data.inspector_name:
            self._log(
                f"⚠ 점검자 '{data.inspector_name}' 이름의 로그인 계정이 등록되어 있지 않습니다. "
                f"'계정 관리'에서 추가하거나, 점검자가 로그인 계정 이름으로 고정되는 점을 감안해 "
                f"현재 선택된 계정으로 진행할지 확인하세요."
            )

    @staticmethod
    def _format_preview(d: K2BSubmissionData) -> str:
        lines = [
            f"현장명: {d.site_name}",
            f"회차: {d.visit_no}",
            f"기술지도일: {d.guidance_date}",
            f"점검자: {d.inspector_name} (⚠ K2B에서 읽기전용 필드 -- 로그인 계정 이름이 자동 적용됨, "
            f"자동입력 안 함)",
            f"현장책임자: {d.site_manager_name} ({d.site_manager_phone})",
            f"공정률: {d.progress_rate}%",
            f"교육인원: {d.education_count}",
            f"현재 작업공정: {d.current_process_name or '(비어있음 -- K2B 드롭다운에서 직접 선택 필요)'}",
            f"통보방법: {d.notification_method or '(비어있음)'}",
            f"이전 기술지도 이행여부: {'이행' if d.prev_guidance_implemented else '불이행' if d.prev_guidance_implemented is not None else '(비어있음)'}",
            f"현장전경 사진: {len(d.overview_photo_paths)}장",
            f"현장점검 사진: {len(d.inspection_photo_paths)}장",
            f"보고서 파일(PDF): {d.report_file_path or '(없음)'}",
            "",
            "※ 아래 항목은 12-1 DB에 없어 자동 입력되지 않습니다 -- K2B 화면에서 직접 확인/입력하세요:",
            "  지도건수, 비계사용현황, 경영책임자/건설업체 본사 통보일, 건설공사 발주자 통보일자",
            "  대형사고 위험작업 (기본값 '해당없음'이라 대부분은 그대로 두면 됨)",
        ]
        return "\n".join(lines)

    def _log(self, msg: str) -> None:
        self.log_area.append(msg)

    # ---------------------------------------------------------- automation

    def _run_automation(self) -> None:
        if self._current_data is None:
            QMessageBox.warning(self, "안내", "먼저 '불러오기'로 데이터를 확인하세요.")
            return
        account_name = self.account_combo.currentText().strip()
        if not account_name:
            QMessageBox.warning(
                self, "안내",
                "로그인 계정이 없습니다. 상단 '계정 관리'에서 K2B 계정을 먼저 등록하세요.",
            )
            return
        creds = get_account(account_name)
        if creds is None:
            QMessageBox.warning(self, "안내", f"'{account_name}' 계정 정보를 찾을 수 없습니다.")
            return
        user_id, password = creds

        self.run_btn.setEnabled(False)
        self._log("K2B 자동입력 시작...")
        self._worker = K2BFillWorker(
            user_id, password, self._current_data, is_new_round=self.new_round_check.isChecked()
        )
        self._worker.log_message.connect(self._log)
        self._worker.failed.connect(self._on_failed)
        self._worker.finished_ok.connect(lambda: self.run_btn.setEnabled(True))
        self._worker.finished.connect(lambda: self.run_btn.setEnabled(True))
        self._worker.start()

    def _on_failed(self, message: str) -> None:
        self._log(f"오류 발생: {message}")
        QMessageBox.critical(self, "오류", f"자동입력 중 오류가 발생했습니다:\n{message}")
        self.run_btn.setEnabled(True)
