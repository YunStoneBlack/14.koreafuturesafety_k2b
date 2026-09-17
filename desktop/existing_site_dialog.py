# -*- coding: utf-8 -*-
"""기존 현장에 보고서(차수) 추가/편집 모달 -- 현장/회차 선택 -> 12-1 DB에서 데이터
로드 -> K2B 자동입력 실행. 예전엔 이 내용이 메인 윈도우 자체였는데, "신규 현장 등록"과
성격이 다른 별도 작업이라 계정 선택 화면(main_window.py)에서 여는 모달로 분리했다
(2026-09-17)."""
from __future__ import annotations

from PyQt6.QtCore import Qt, QDate
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTextEdit, QComboBox, QCheckBox, QMessageBox,
    QDateEdit, QListWidget, QTableWidget, QHeaderView,
    QAbstractItemView, QScrollArea, QWidget,
)

from core import k2b_selectors as sel
from core.config import REPORT_APP_DB_PATH
from core.credentials import get_account
from core.db_reader import (
    K2BSubmissionData, MajorHazardWork, get_submission_data, list_rounds, list_sites,
)
from .bad_site_drop_zone import BadSiteFileDropZone
from .gui_style import make_card, section_title, field_label
from .worker import K2BFillWorker

_NOT_SELECTED = "(선택 안 함)"


class ExistingSiteDialog(QDialog):
    def __init__(self, account_name: str, parent=None):
        super().__init__(parent)
        self.account_name = account_name
        self.setWindowTitle(f"기존 현장에 보고서 추가 등록 — 로그인 계정: {account_name}")
        self.resize(880, 780)
        self.setMinimumSize(720, 480)
        self.setSizeGripEnabled(True)  # 우측 하단 크기조절 그립 -- 독립적으로 크기조절 가능

        self._current_data: K2BSubmissionData | None = None
        self._worker: K2BFillWorker | None = None

        self._build_ui()
        self._reload_site_list()

    # ------------------------------------------------------------------ UI

    def _build_ui(self) -> None:
        # 카드가 여러 개(제출대상/K2B 전용 항목/미리보기/로그)라 창 높이에 다 안 들어갈
        # 수 있다 -- 위쪽 입력 카드들만 스크롤 영역에 담고, 실행 버튼/경고문구/안내문구는
        # 스크롤 밖 하단에 고정해서 창을 작게 줄여도 항상 보이게 한다(예전 메인윈도우에
        # 있던 패턴인데 모달로 분리하면서 빠뜨렸던 것 -- 2026-09-17 실사용 중 발견해 복구).
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        content = QWidget()
        root = QVBoxLayout(content)
        root.setContentsMargins(24, 20, 24, 16)
        root.setSpacing(16)
        scroll.setWidget(content)
        outer.addWidget(scroll, stretch=1)

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

        root.addWidget(self._build_manual_fields_card())

        card2, l2 = make_card()
        l2.addWidget(section_title("K2B에 입력될 내용 미리보기"))
        self.preview = QTextEdit()
        self.preview.setReadOnly(True)
        self.preview.setFixedHeight(200)
        l2.addWidget(self.preview)
        root.addWidget(card2)

        card3, l3 = make_card()
        l3.addWidget(section_title("실행 로그"))
        self.log_area = QTextEdit()
        self.log_area.setObjectName("LogArea")
        self.log_area.setReadOnly(True)
        self.log_area.setFixedHeight(140)
        l3.addWidget(self.log_area)
        root.addWidget(card3)

        # 실행 버튼 영역은 스크롤 밖(outer)에 고정 배치 -- 창을 작게 줄이거나 내용이
        # 늘어나도 항상 화면에 보이게 한다.
        bottom = QWidget()
        bottom_layout = QVBoxLayout(bottom)
        bottom_layout.setContentsMargins(24, 12, 24, 16)
        bottom_layout.setSpacing(10)

        action_row = QHBoxLayout()
        self.new_round_check = QCheckBox("새 차수로 추가 (K2B에 이 회차가 아직 없음)")
        self.new_round_check.setChecked(True)  # 기본값 체크 -- 꺼두면 K2B에 현재 열려있는
        # 기존 차수를 그대로 덮어쓰게 되는데, 12-1의 회차 번호와 K2B의 차수 번호는 서로
        # 무관한 별개 카운터라 실수로 엉뚱한 기존 데이터를 덮어쓸 위험이 있다(실사용 중
        # 발견). 게다가 기존 차수는 "보고서 수정가능 기한"(기술지도일+7일)이 이미 지나
        # 있을 수 있어 파일첨부 자체가 막힌다. 새 차수는 기술지도일이 오늘로 자동
        # 설정되어 이 문제가 없다 -- 기존 차수를 의도적으로 고칠 때만 체크 해제할 것.
        self.new_round_check.toggled.connect(self._on_new_round_toggled)
        action_row.addWidget(self.new_round_check)
        action_row.addStretch()
        self.stop_btn = QPushButton("중단")
        self.stop_btn.setObjectName("DangerButton")
        self.stop_btn.setEnabled(False)
        self.stop_btn.clicked.connect(self._stop_automation)
        action_row.addWidget(self.stop_btn)
        self.run_btn = QPushButton("K2B 화면에 자동 입력하기")
        self.run_btn.setObjectName("PrimaryButton")
        self.run_btn.clicked.connect(self._run_automation)
        action_row.addWidget(self.run_btn)
        bottom_layout.addLayout(action_row)

        self.overwrite_warning = QLabel(
            "⚠ 체크 해제됨: 새 차수를 만들지 않고 K2B에 현재 열려있는 기존 차수를 그대로 "
            "덮어씁니다. 의도한 게 맞는지 다시 확인하세요."
        )
        self.overwrite_warning.setObjectName("WarningLabel")
        self.overwrite_warning.setWordWrap(True)
        self.overwrite_warning.setVisible(False)
        bottom_layout.addWidget(self.overwrite_warning)

        footer = QLabel("이 프로그램은 최종 저장(제출) 버튼을 자동으로 누르지 않습니다 — "
                         "화면을 확인한 뒤 직접 클릭하세요.")
        footer.setObjectName("FooterLabel")
        footer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        bottom_layout.addWidget(footer)

        outer.addWidget(bottom)

    def _on_new_round_toggled(self, checked: bool) -> None:
        self.overwrite_warning.setVisible(not checked)

    def _build_manual_fields_card(self):
        """보고서와 자동 연동이 안 되거나(현재 작업공종/비계사용현황), K2B 전용이라
        12-1 DB에 대응 값이 아예 없는(불량사업장 통보/대형사고 위험작업) 항목들을
        사람이 앱에서 직접 고르는 카드. 여기서 고른 값은 `_apply_manual_fields()`가
        실행 직전에 `K2BSubmissionData`에 반영한다."""
        card, layout = make_card()
        layout.addWidget(section_title("K2B 전용 항목 (보고서와 자동 연동 안 됨 — 직접 선택)"))

        row1 = QHBoxLayout()
        row1.addWidget(field_label("현재 작업공종"))
        self.current_process_combo = QComboBox()
        self.current_process_combo.addItem(_NOT_SELECTED)
        self.current_process_combo.addItems(sel.CURRENT_PROCESS_OPTIONS)
        row1.addWidget(self.current_process_combo, stretch=1)
        layout.addLayout(row1)

        row2 = QHBoxLayout()
        row2.addWidget(field_label("비계사용현황"))
        self.scaffold_usage_combo = QComboBox()
        self.scaffold_usage_combo.addItems([_NOT_SELECTED, "사용", "미사용"])
        self.scaffold_usage_combo.currentTextChanged.connect(self._on_scaffold_usage_changed)
        row2.addWidget(self.scaffold_usage_combo)
        row2.addWidget(field_label("비계종류"))
        self.scaffold_type_checks: dict[str, QCheckBox] = {}
        for name in sel.SCAFFOLD_TYPE_CHECKBOX_IDS:
            box = QCheckBox(name)
            box.setEnabled(False)
            self.scaffold_type_checks[name] = box
            row2.addWidget(box)
        row2.addStretch()
        layout.addLayout(row2)

        # --- 불량사업장 통보 ---
        self.bad_site_check = QCheckBox("불량사업장 통보")
        self.bad_site_check.toggled.connect(self._on_bad_site_toggled)
        layout.addWidget(self.bad_site_check)

        self.bad_site_content = QTextEdit()
        self.bad_site_content.setPlaceholderText("신고내용을 입력해 주십시요")
        self.bad_site_content.setFixedHeight(60)
        self.bad_site_content.setEnabled(False)
        layout.addWidget(self.bad_site_content)

        bad_site_files_row = QHBoxLayout()
        self.bad_site_drop_zone = BadSiteFileDropZone()
        self.bad_site_drop_zone.setEnabled(False)
        self.bad_site_drop_zone.files_selected.connect(self._on_bad_site_files_selected)
        bad_site_files_row.addWidget(self.bad_site_drop_zone, stretch=1)

        bad_site_file_col = QVBoxLayout()
        self.bad_site_file_list = QListWidget()
        self.bad_site_file_list.setEnabled(False)
        self.bad_site_file_list.setFixedHeight(80)
        bad_site_file_col.addWidget(self.bad_site_file_list)
        self.bad_site_remove_file_btn = QPushButton("선택 파일 제거")
        self.bad_site_remove_file_btn.setObjectName("SecondaryButton")
        self.bad_site_remove_file_btn.setEnabled(False)
        self.bad_site_remove_file_btn.clicked.connect(self._remove_selected_bad_site_file)
        bad_site_file_col.addWidget(self.bad_site_remove_file_btn)
        bad_site_files_row.addLayout(bad_site_file_col, stretch=1)
        layout.addLayout(bad_site_files_row)

        # --- 대형사고 위험작업 ---
        layout.addWidget(field_label(
            "대형사고 위험작업 (기본값은 K2B의 '해당없음' 체크 — 추가하지 않으면 그대로 둡니다)"
        ))
        self.hazard_table = QTableWidget(0, 4)
        self.hazard_table.setHorizontalHeaderLabels(["발생형태", "대형사고 위험작업", "시작일", "종료일"])
        self.hazard_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.hazard_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.hazard_table.setFixedHeight(140)
        layout.addWidget(self.hazard_table)

        hazard_btn_row = QHBoxLayout()
        hazard_add_btn = QPushButton("+ 추가")
        hazard_add_btn.setObjectName("SecondaryButton")
        hazard_add_btn.clicked.connect(self._add_hazard_row)
        hazard_btn_row.addWidget(hazard_add_btn)
        hazard_remove_btn = QPushButton("선택 행 제거")
        hazard_remove_btn.setObjectName("SecondaryButton")
        hazard_remove_btn.clicked.connect(self._remove_hazard_row)
        hazard_btn_row.addWidget(hazard_remove_btn)
        hazard_btn_row.addStretch()
        layout.addLayout(hazard_btn_row)

        return card

    def _on_scaffold_usage_changed(self, text: str) -> None:
        enabled = text == "사용"
        for box in self.scaffold_type_checks.values():
            box.setEnabled(enabled)
            if not enabled:
                box.setChecked(False)

    def _on_bad_site_toggled(self, checked: bool) -> None:
        self.bad_site_content.setEnabled(checked)
        self.bad_site_drop_zone.setEnabled(checked)
        self.bad_site_file_list.setEnabled(checked)
        self.bad_site_remove_file_btn.setEnabled(checked)

    def _on_bad_site_files_selected(self, paths: list[str]) -> None:
        for p in paths:
            self.bad_site_file_list.addItem(p)

    def _remove_selected_bad_site_file(self) -> None:
        for item in self.bad_site_file_list.selectedItems():
            self.bad_site_file_list.takeItem(self.bad_site_file_list.row(item))

    def _add_hazard_row(self) -> None:
        row = self.hazard_table.rowCount()
        self.hazard_table.insertRow(row)

        occurrence_combo = QComboBox()
        occurrence_combo.addItems(sel.MAJOR_HAZARD_WORK_OCCURRENCE_TYPES)
        self.hazard_table.setCellWidget(row, 0, occurrence_combo)

        work_combo = QComboBox()
        occurrence_combo.currentTextChanged.connect(
            lambda text, combo=work_combo: self._refresh_hazard_work_options(combo, text)
        )
        self._refresh_hazard_work_options(work_combo, occurrence_combo.currentText())
        self.hazard_table.setCellWidget(row, 1, work_combo)

        today = QDate.currentDate()
        start_edit = QDateEdit(today)
        start_edit.setCalendarPopup(True)
        start_edit.setDisplayFormat("yyyy-MM-dd")
        self.hazard_table.setCellWidget(row, 2, start_edit)

        end_edit = QDateEdit(today)
        end_edit.setCalendarPopup(True)
        end_edit.setDisplayFormat("yyyy-MM-dd")
        self.hazard_table.setCellWidget(row, 3, end_edit)

    def _refresh_hazard_work_options(self, work_combo: QComboBox, occurrence_type: str) -> None:
        """발생형태 선택에 따라 대형사고위험작업 드롭다운을 (사이트와 동일하게) 다시
        채운다 -- 항상 "선택" 플레이스홀더가 기본값이 되도록 초기화한다."""
        work_combo.blockSignals(True)
        work_combo.clear()
        work_combo.addItem(_NOT_SELECTED)
        work_combo.addItems(sel.MAJOR_HAZARD_WORK_OPTIONS_BY_OCCURRENCE.get(occurrence_type, []))
        work_combo.setCurrentIndex(0)
        work_combo.blockSignals(False)

    def _remove_hazard_row(self) -> None:
        rows = sorted({idx.row() for idx in self.hazard_table.selectedIndexes()}, reverse=True)
        for row in rows:
            self.hazard_table.removeRow(row)

    def _apply_manual_fields(self, data: K2BSubmissionData) -> None:
        """이 카드에서 사람이 고른 값들을 자동입력 직전에 데이터에 반영한다."""
        if self.current_process_combo.currentText() != _NOT_SELECTED:
            data.current_process_name = self.current_process_combo.currentText()

        usage = self.scaffold_usage_combo.currentText()
        if usage != _NOT_SELECTED:
            data.scaffold_usage = usage
            data.scaffold_types = [
                name for name, box in self.scaffold_type_checks.items() if box.isChecked()
            ]

        data.bad_site_notify = self.bad_site_check.isChecked()
        if data.bad_site_notify:
            data.bad_site_notify_content = self.bad_site_content.toPlainText().strip()
            data.bad_site_notify_files = [
                self.bad_site_file_list.item(i).text() for i in range(self.bad_site_file_list.count())
            ]

        hazard_works: list[MajorHazardWork] = []
        for row in range(self.hazard_table.rowCount()):
            occurrence_combo = self.hazard_table.cellWidget(row, 0)
            work_combo = self.hazard_table.cellWidget(row, 1)
            start_edit = self.hazard_table.cellWidget(row, 2)
            end_edit = self.hazard_table.cellWidget(row, 3)
            if work_combo.currentText() == _NOT_SELECTED:
                self._log(f"⚠ 대형사고 위험작업 {row + 1}행: 종류를 선택하지 않아 건너뜁니다.")
                continue
            hazard_works.append(MajorHazardWork(
                occurrence_type=occurrence_combo.currentText(),
                hazard_work=work_combo.currentText(),
                start_date=start_edit.date().toString("yyyy-MM-dd"),
                end_date=end_edit.date().toString("yyyy-MM-dd"),
            ))
        data.major_hazard_works = hazard_works

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

        # 현재 작업공종은 보고서와 자동 연동이 안 돼 항상 사람이 골라야 하지만, 혹시
        # 12-1 DB 값이 K2B의 7종 중 하나와 우연히 일치하면 편의상 미리 선택해둔다.
        idx = self.current_process_combo.findText(data.current_process_name)
        self.current_process_combo.setCurrentIndex(idx if idx >= 0 else 0)

        if data.inspector_name and data.inspector_name != self.account_name:
            self._log(
                f"⚠ 점검자 '{data.inspector_name}'와 현재 로그인 계정('{self.account_name}') "
                f"이름이 다릅니다. K2B에서 점검자는 로그인 계정 이름으로 고정되는 읽기전용 "
                f"필드라 이대로 진행하면 '{self.account_name}'으로 기록됩니다."
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
            f"통보방법: {d.notification_method or '(비어있음)'}",
            f"이전 기술지도 이행여부: {'이행' if d.prev_guidance_implemented else '불이행' if d.prev_guidance_implemented is not None else '(비어있음)'}",
            f"현장전경 사진: {len(d.overview_photo_paths)}장",
            f"현장점검 사진: {len(d.inspection_photo_paths)}장",
            f"현장개선 사진: {len(d.improvement_photo_paths)}장",
            f"보고서 파일(PDF): {d.report_file_path or '(없음)'}",
            "",
            "※ 현재 작업공종/비계사용현황/불량사업장 통보/대형사고 위험작업은 보고서와 자동",
            "  연동되지 않습니다 -- 아래 'K2B 전용 항목' 카드에서 직접 선택하세요.",
            "※ 아래 항목은 12-1 DB에 대응 값이 없어 자동 입력되지 않습니다 -- K2B 화면에서",
            "  직접 확인/입력하세요: 지도건수, 경영책임자/건설업체 본사 통보일, 건설공사",
            "  발주자 통보일자",
        ]
        return "\n".join(lines)

    def _log(self, msg: str) -> None:
        self.log_area.append(msg)

    # ---------------------------------------------------------- automation

    def _run_automation(self) -> None:
        if self._current_data is None:
            QMessageBox.warning(self, "안내", "먼저 '불러오기'로 데이터를 확인하세요.")
            return
        creds = get_account(self.account_name)
        if creds is None:
            QMessageBox.warning(self, "안내", f"'{self.account_name}' 계정 정보를 찾을 수 없습니다.")
            return
        user_id, password = creds

        d = self._current_data
        is_new_round = self.new_round_check.isChecked()
        summary = (
            f"현장명: {d.site_name}\n"
            f"회차: {d.visit_no}\n"
            f"로그인 계정: {self.account_name}\n\n"
            + ("새 차수로 추가합니다." if is_new_round
               else "⚠ 새 차수를 만들지 않고 기존 차수를 그대로 덮어씁니다.")
            + "\n\n이 내용으로 K2B 자동입력을 시작할까요?"
        )
        reply = QMessageBox.question(
            self, "실행 확인", summary,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return

        self._apply_manual_fields(d)

        self.run_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self._log("K2B 자동입력 시작...")
        self._worker = K2BFillWorker(user_id, password, d, is_new_round=is_new_round)
        self._worker.log_message.connect(self._log)
        self._worker.failed.connect(self._on_failed)
        self._worker.finished_ok.connect(lambda: self.run_btn.setEnabled(True))
        self._worker.finished.connect(self._on_worker_finished)
        self._worker.start()

    def _stop_automation(self) -> None:
        if self._worker is not None:
            self._worker.request_stop()
            self.stop_btn.setEnabled(False)

    def _on_worker_finished(self) -> None:
        self.run_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)

    def _on_failed(self, message: str) -> None:
        self._log(f"오류 발생: {message}")
        QMessageBox.critical(self, "오류", f"자동입력 중 오류가 발생했습니다:\n{message}")
        self.run_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
