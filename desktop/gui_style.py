# -*- coding: utf-8 -*-
"""스타일시트, 아이콘, 카드형 레이아웃 헬퍼.

디자인은 회사의 이전 프로젝트들(네이버쇼핑검색데이터수집/네이버부동산크롤링/카카오톡
자동화/구글메시지 자동화)의 gui.py 스타일(카드형 레이아웃, 라벤더/퍼플 톤, 둥근 모서리)을
그대로 따른다 — 사내 프로그램군 전체의 시각적 일관성을 위해 스타일시트 문자열 자체를
그대로 재사용한다(원본: 11번 프로젝트 app/gui_style.py).
"""
import sys
from pathlib import Path

from PyQt6.QtCore import Qt, QPointF
from PyQt6.QtGui import QFont, QIcon, QPixmap, QPainter, QColor, QPolygonF
from PyQt6.QtWidgets import QFrame, QVBoxLayout, QLabel

from .core import PROJECT_ROOT
from .gui_constants import ASSETS_DIR

# ---------------------------------------------------------------------------
# 스타일시트 (참고 디자인: 카드형 레이아웃, 둥근 모서리, 라벤더/퍼플 톤)
# ---------------------------------------------------------------------------

STYLE_SHEET_TEMPLATE = """
QWidget#Central { background-color: #F5F3FB; }

QFrame[class="card"] {
    background-color: #FFFFFF;
    border: 1px solid #E5DFF5;
    border-radius: 12px;
}
QLabel[class="section-title"] { font-size: 15px; font-weight: 600; color: #221D33; }
QLabel[class="field-label"] { font-size: 12px; color: #6B6483; }

QLineEdit, QDoubleSpinBox, QComboBox, QDateEdit {
    border: 1px solid #DDD5F2;
    border-radius: 8px;
    padding: 8px 10px;
    font-size: 13px;
    background: #FFFFFF;
    color: #221D33;
}
QLineEdit:focus, QDoubleSpinBox:focus, QComboBox:focus, QDateEdit:focus { border: 1px solid #6C4FF0; }

QDoubleSpinBox { padding-right: 4px; }
QDoubleSpinBox::up-button, QDoubleSpinBox::down-button {
    subcontrol-origin: border;
    width: 22px;
    border: none;
    border-left: 1px solid #DDD5F2;
    background: #F4F1FB;
}
QDoubleSpinBox::up-button {
    subcontrol-position: top right;
    border-top-right-radius: 8px;
    margin-top: 1px;
}
QDoubleSpinBox::down-button {
    subcontrol-position: bottom right;
    border-bottom-right-radius: 8px;
    margin-bottom: 1px;
}
QDoubleSpinBox::up-button:hover, QDoubleSpinBox::down-button:hover { background: #EDE7FB; }
QDoubleSpinBox::up-button:pressed, QDoubleSpinBox::down-button:pressed { background: #E1D8F8; }
QDoubleSpinBox::up-arrow {
    image: url(__ARROW_UP_URL__);
    width: 9px;
    height: 9px;
}
QDoubleSpinBox::down-arrow {
    image: url(__ARROW_DOWN_URL__);
    width: 9px;
    height: 9px;
}

QCheckBox { font-size: 13px; color: #221D33; spacing: 6px; }
QCheckBox::indicator {
    width: 16px; height: 16px;
    border: 1px solid #DDD5F2;
    border-radius: 4px;
    background: #FFFFFF;
}
QCheckBox::indicator:checked { background: #6C4FF0; border: 1px solid #6C4FF0; }

/* QTableWidget 행 선택용 체크박스(아이템 체크박스)도 앱 전역에 스타일시트를 적용하는
순간부터는 네이티브 렌더링 대신 이 스타일 엔진을 타는데, 여기에 전용 규칙이 없으면
체크 여부와 무관하게 빈 사각형만 그려져 체크 상태가 화면에 전혀 표시되지 않는
문제가 있었다(11번 프로젝트 실사용 중 발견) - QCheckBox::indicator와 같은 톤으로 별도 정의한다. */
QTableWidget::indicator {
    width: 16px; height: 16px;
    border: 1px solid #DDD5F2;
    border-radius: 4px;
    background: #FFFFFF;
}
QTableWidget::indicator:checked { background: #6C4FF0; border: 1px solid #6C4FF0; }

QPushButton#PrimaryButton {
    background-color: #6C4FF0;
    color: white;
    border: none;
    border-radius: 8px;
    padding: 12px;
    font-size: 14px;
    font-weight: 600;
}
QPushButton#PrimaryButton:hover:!disabled { background-color: #5A3FDB; }
QPushButton#PrimaryButton:disabled { background-color: #C9B8F5; }

QPushButton#SecondaryButton {
    background-color: #F5F3FB;
    color: #4A4360;
    border: 1px solid #DDD5F2;
    border-radius: 8px;
    padding: 10px 12px;
    font-size: 13px;
}
QPushButton#SecondaryButton:hover:!disabled { background-color: #EEEAF9; }
QPushButton#SecondaryButton:disabled { color: #A79FC0; }

QPushButton#DangerButton {
    background-color: #FFFFFF;
    color: #D14343;
    border: 1px solid #F3C6C6;
    border-radius: 8px;
    padding: 10px 12px;
    font-size: 13px;
}
QPushButton#DangerButton:hover:!disabled { background-color: #FDEDED; }
QPushButton#DangerButton:disabled { color: #C9A9A9; border: 1px solid #EEE0E0; }

QLabel#WarningLabel { color: #D14343; font-size: 12px; font-weight: 600; }

QProgressBar {
    border: none;
    border-radius: 8px;
    background-color: #EEEAF9;
    text-align: center;
    height: 26px;
    font-weight: 600;
    color: #221D33;
}
QProgressBar::chunk { background-color: #6C4FF0; border-radius: 8px; }

QTextEdit#LogArea {
    border: 1px solid #E5DFF5;
    border-radius: 8px;
    background-color: #FAF9FE;
    font-family: Consolas, monospace;
    font-size: 12px;
    color: #4A4360;
}

QTableWidget {
    border: 1px solid #E5DFF5;
    border-radius: 8px;
    gridline-color: #EFE9FA;
    font-size: 12px;
    background-color: #FFFFFF;
}
QHeaderView::section {
    background-color: #F4F1FB;
    padding: 6px;
    border: none;
    border-bottom: 1px solid #E5DFF5;
    font-weight: 600;
    color: #5C5578;
}

QLabel#FooterLabel { color: #A79FC0; font-size: 11px; }
QLabel#StatusDot { font-size: 20px; }
"""


def _draw_triangle_icon(path, direction: str, color: str = "#6B6483"):
    size = 16
    pix = QPixmap(size, size)
    pix.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pix)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setBrush(QColor(color))
    painter.setPen(Qt.PenStyle.NoPen)
    if direction == "down":
        points = [QPointF(3, 5), QPointF(13, 5), QPointF(8, 12)]
    else:
        points = [QPointF(3, 11), QPointF(13, 11), QPointF(8, 4)]
    painter.drawPolygon(QPolygonF(points))
    painter.end()
    pix.save(str(path))


def generate_arrow_icons() -> tuple[str, str]:
    ASSETS_DIR.mkdir(exist_ok=True)
    up_path = ASSETS_DIR / "arrow_up.png"
    down_path = ASSETS_DIR / "arrow_down.png"
    if not up_path.exists():
        _draw_triangle_icon(up_path, "up")
    if not down_path.exists():
        _draw_triangle_icon(down_path, "down")
    return up_path.as_posix(), down_path.as_posix()


def build_style_sheet() -> str:
    up_url, down_url = generate_arrow_icons()
    return (
        STYLE_SHEET_TEMPLATE
        .replace("__ARROW_UP_URL__", up_url)
        .replace("__ARROW_DOWN_URL__", down_url)
    )


def resource_path(name: str) -> Path:
    """아이콘 등 읽기전용 번들 리소스 경로. exe로 빌드되면 __file__은 PyInstaller가
    압축 해제한 임시 폴더(_MEIPASS)를 가리키므로 그쪽을, 소스 실행 중이면 프로젝트 루트를 본다."""
    base = Path(getattr(sys, "_MEIPASS", PROJECT_ROOT))
    return base / name


def make_window_icon() -> QIcon:
    icon_path = resource_path("icon.ico")
    if icon_path.exists():
        return QIcon(str(icon_path))
    pix = QPixmap(64, 64)
    pix.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pix)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setBrush(QColor("#6C4FF0"))
    painter.setPen(Qt.PenStyle.NoPen)
    painter.drawRoundedRect(0, 0, 64, 64, 16, 16)
    painter.setPen(QColor("white"))
    painter.setFont(QFont("Segoe UI Emoji", 28))
    painter.drawText(pix.rect(), Qt.AlignmentFlag.AlignCenter, "\U0001F4E4")  # 📤 (제출/전송)
    painter.end()
    return QIcon(pix)


def make_card() -> tuple:
    frame = QFrame()
    frame.setProperty("class", "card")
    layout = QVBoxLayout(frame)
    layout.setContentsMargins(20, 18, 20, 18)
    layout.setSpacing(12)
    return frame, layout


def section_title(text: str) -> QLabel:
    lbl = QLabel(text)
    lbl.setProperty("class", "section-title")
    return lbl


def field_label(text: str) -> QLabel:
    lbl = QLabel(text)
    lbl.setProperty("class", "field-label")
    return lbl
