"""불량사업장 통보 첨부파일을 드래그앤드롭 또는 "파일 선택"으로 고르는 위젯.

12-1 프로젝트의 `pdf_drop_zone.py` 패턴을 그대로 따르되, K2B 화면이 실제로 받는 확장자
(jpg/jpeg/gif/png/bmp/pdf, 실화면 "불량사업장 사진 및 보고서 첨부" 버튼 안내문구로 CONFIRMED)
에 맞게 여러 확장자를 허용하도록 일반화했다.
"""

from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import QFileDialog, QFrame, QHBoxLayout, QLabel, QMessageBox, QPushButton, QVBoxLayout

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".gif", ".png", ".bmp", ".pdf"}
_FILE_FILTER = "허용 파일 (*.jpg *.jpeg *.gif *.png *.bmp *.pdf)"


class BadSiteFileDropZone(QFrame):
    files_selected = pyqtSignal(list)  # list[str] — 확장자 검사를 통과한 경로만 담긴다

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setStyleSheet(
            "QFrame { border: 2px dashed #DDD5F2; border-radius: 10px; background: #FAF9FE; }"
        )

        layout = QVBoxLayout(self)
        layout.setSpacing(6)
        layout.setContentsMargins(16, 18, 16, 18)

        title = QLabel("파일을 여기로 드래그하거나 선택하세요")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 13px; font-weight: 600; border: none; background: transparent; color: #221D33;")
        layout.addWidget(title)

        sub = QLabel("jpg, jpeg, gif, png, bmp, pdf만 가능")
        sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sub.setStyleSheet("color: #A79FC0; font-size: 11px; border: none; background: transparent;")
        layout.addWidget(sub)

        browse_btn = QPushButton("파일 선택")
        browse_btn.setObjectName("SecondaryButton")
        browse_btn.clicked.connect(self._browse)
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        btn_row.addWidget(browse_btn)
        btn_row.addStretch()
        layout.addLayout(btn_row)

    def dragEnterEvent(self, event) -> None:  # noqa: N802 (Qt override)
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event) -> None:  # noqa: N802 (Qt override)
        paths = [url.toLocalFile() for url in event.mimeData().urls()]
        self._emit_valid(paths)

    def _browse(self) -> None:
        paths, _ = QFileDialog.getOpenFileNames(self, "첨부파일 선택", "", _FILE_FILTER)
        if paths:
            self._emit_valid(paths)

    def _emit_valid(self, paths: list[str]) -> None:
        valid: list[str] = []
        rejected: list[str] = []
        for p in paths:
            path = Path(p)
            if path.suffix.lower() not in ALLOWED_EXTENSIONS:
                rejected.append(f"{path.name} (허용되지 않는 형식)")
                continue
            valid.append(p)
        if rejected:
            QMessageBox.warning(self, "일부 파일 제외됨", "다음 파일은 제외했습니다:\n" + "\n".join(rejected))
        if valid:
            self.files_selected.emit(valid)
