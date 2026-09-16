"""12-1 프로젝트(app.db)에서 K2B 제출에 필요한 회차 데이터를 읽어온다.

12-1의 SQLAlchemy 모델을 그대로 import하지 않고 raw sqlite3로 직접 읽는다 — 두 프로젝트가
서로 다른 경로/배포 형태(하나는 데스크톱 exe, 하나는 나중에 서버)를 갖게 될 것이므로,
12-1의 내부 패키지 구조가 바뀌어도 이쪽이 깨지지 않도록 스키마 의존만 남겨둔다.
읽기 전용(mode=ro)으로 열어서 실수로 원본 DB를 건드릴 일이 없다.

주의: 아래 필드 중 일부는 12-1 DB에 대응 컬럼이 없다(K2B 전용 필드). 이런 필드는
K2BSubmissionData에서 기본값(None/기본)으로 두고, 실제 사용 시점엔 화면에서 사람이
직접 입력하거나 확인해야 한다 -- 존재하지 않는 값을 추측해서 채우지 않는다.
"""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class MajorHazardWork:
    """대형사고 위험작업 한 행. "업무영역"은 K2B가 행 추가 시 자동으로 채우는 고정값이라
    (실화면 확인) 여기서 다루지 않는다 -- 발생형태/위험작업 종류/예정시기(시작~종료)만
    사람이 앱에서 직접 고른다."""

    occurrence_type: str  # 발생형태: 전체/붕괴/도괴/낙하/질식 중 하나
    hazard_work: str  # k2b_selectors.MAJOR_HAZARD_WORK_OPTIONS 중 하나
    start_date: str  # YYYY-MM-DD
    end_date: str  # YYYY-MM-DD


@dataclass
class K2BSubmissionData:
    # --- 12-1 DB에서 그대로 가져오는 값 ---
    site_name: str = ""
    site_mgmt_no: str = ""  # Site.site_mgmt_no (사업장관리번호)
    management_no: str = ""  # Site.management_no (K2B 관리번호, 1회차 저장 후 채워짐)
    visit_no: int | None = None  # 차수
    guidance_date: str | None = None  # YYYY-MM-DD
    inspector_name: str = ""  # 점검자 (담당요원)
    site_manager_name: str = ""  # 현장책임자명
    site_manager_phone: str = ""  # 현장책임자 연락처
    progress_rate: int | None = None  # 공정률(%)
    education_count: int | None = None  # 교육인원 (SafetyEducation.attendee_count)
    distributed_material_count: int = 0  # 배포자료건수 (ProvidedMaterial 실채움 개수)
    current_process_name: str = ""  # 현재 작업공정
    special_note: str = ""  # 특이사항
    notification_method: str = ""  # 직접전달/등기우편/전자우편/모바일/기타
    prev_guidance_implemented: bool | None = None  # 이전 기술지도 이행여부
    overview_photo_paths: list[str] = field(default_factory=list)  # 현장전경 사진
    inspection_photo_paths: list[str] = field(default_factory=list)  # 현장점검 사진
    improvement_photo_paths: list[str] = field(default_factory=list)  # 현장개선 사진

    # 보고서 파일 -- K2B는 HWP/HWPX 첨부가 안 되고 PDF만 받는 것으로 실사용 중 확인됨
    # (CONFIRMED). report_file_path는 항상 report_pdf_path를 쓴다. report_hwpx_path는
    # 참고용으로만 남겨둠(다른 용도로 필요할 수 있어 보관).
    report_pdf_path: str = ""
    report_hwpx_path: str = ""
    report_file_path: str = ""  # = report_pdf_path (K2B는 PDF만 받음, CONFIRMED)

    # --- 12-1 DB에 대응 항목이 없어(또는 보고서 문구가 K2B 옵션과 안 맞아) 앱 화면에서
    # 직접 선택해야 하는 값. main_window.py의 UI가 이 필드들을 직접 채운다. ---
    guidance_count: int | None = None  # 지도건수 -- 대응 컬럼 없음
    scaffold_usage: str | None = None  # "사용" | "미사용" | None(선택 안 함)
    scaffold_types: list[str] = field(default_factory=list)  # 비계종류(강관비계/시스템비계), 사용일 때만 의미 있음
    owner_notify_date: str | None = None  # 건설공사 발주자 통보일자 -- 대응 컬럼 없음
    hq_notify_quarter: str | None = None  # 경영책임자/건설업체 본사 통보 분기 -- 대응 컬럼 없음
    major_hazard_works: list[MajorHazardWork] = field(default_factory=list)  # 대형사고 위험작업

    # 불량사업장 통보 -- 보고서와 연동되지 않아 앱에서 직접 체크/입력.
    bad_site_notify: bool = False
    bad_site_notify_content: str = ""
    bad_site_notify_files: list[str] = field(default_factory=list)  # jpg/jpeg/gif/png/bmp/pdf만 허용(K2B 제약)


def _connect_readonly(db_path: str | Path) -> sqlite3.Connection:
    uri = f"file:{Path(db_path).as_posix()}?mode=ro"
    conn = sqlite3.connect(uri, uri=True)
    conn.row_factory = sqlite3.Row
    return conn


def _resolve_path(db_path: str | Path, stored: str) -> str:
    """DB에 저장된 파일 경로를 실제 경로로 바꾼다.

    개발 중인 12-1 DB는 절대경로를 그대로 쓰지만(예: "C:\\Users\\...\\report_6.pdf"),
    exe 배포판에 같이 넣는 데모 DB는 폴더째로 옮겨도 안 깨지도록 **DB 파일 기준 상대경로**
    (예: "report_6.pdf")로 저장해둔다. 절대경로면 그대로, 상대경로면 db_path의 폴더
    기준으로 풀어서 반환한다."""
    if not stored:
        return ""
    p = Path(stored)
    if p.is_absolute():
        return stored
    return str((Path(db_path).parent / p).resolve())


def get_submission_data(
    db_path: str | Path, site_name: str, visit_no: int | None = None
) -> K2BSubmissionData | None:
    """현장명(+선택적으로 차수)으로 회차 데이터를 조회한다.

    visit_no를 지정하지 않으면 해당 현장의 가장 최근(visit_no 최대) 회차를 가져온다.
    일치하는 현장/회차가 없으면 None.
    """
    conn = _connect_readonly(db_path)
    try:
        site_row = conn.execute(
            "SELECT * FROM site WHERE name = ? ORDER BY id DESC LIMIT 1", (site_name,)
        ).fetchone()
        if site_row is None:
            return None

        if visit_no is not None:
            report_row = conn.execute(
                "SELECT * FROM report WHERE site_id = ? AND visit_no = ?",
                (site_row["id"], visit_no),
            ).fetchone()
        else:
            report_row = conn.execute(
                "SELECT * FROM report WHERE site_id = ? ORDER BY visit_no DESC LIMIT 1",
                (site_row["id"],),
            ).fetchone()
        if report_row is None:
            return None

        report_id = report_row["id"]

        inspector_name = ""
        staff_id = report_row["assigned_staff_id"]
        if staff_id is not None:
            staff_row = conn.execute(
                "SELECT name FROM staff WHERE id = ?", (staff_id,)
            ).fetchone()
            if staff_row is not None:
                inspector_name = staff_row["name"]

        education_row = conn.execute(
            "SELECT attendee_count FROM safety_education WHERE report_id = ?", (report_id,)
        ).fetchone()
        education_count = education_row["attendee_count"] if education_row is not None else None

        material_count = conn.execute(
            """SELECT COUNT(*) AS cnt FROM provided_material
               WHERE report_id = ? AND (material_id IS NOT NULL OR custom_photo_path != '')""",
            (report_id,),
        ).fetchone()["cnt"]

        overview_photos = [
            _resolve_path(db_path, row["photo_path"])
            for row in conn.execute(
                """SELECT photo_path FROM overview_photo
                   WHERE report_id = ? AND photo_path != '' ORDER BY slot""",
                (report_id,),
            )
        ]
        inspection_photos = [
            _resolve_path(db_path, row["photo_path"])
            for row in conn.execute(
                """SELECT photo_path FROM inspection_photo
                   WHERE report_id = ? AND photo_path != '' ORDER BY slot""",
                (report_id,),
            )
        ]
        # 현장개선사진 = "이전지적사항"의 조치완료 증빙사진(previous_finding.completion_photo_path).
        # 12-1의 보고서 생성 코드도 result_status와 무관하게 이 값이 있으면 그대로 삽입하므로
        # (report_builder_hwpx_images.py 참고) 여기서도 값 존재 여부만으로 필터링한다.
        improvement_photos = [
            _resolve_path(db_path, row["completion_photo_path"])
            for row in conn.execute(
                """SELECT completion_photo_path FROM previous_finding
                   WHERE report_id = ? AND completion_photo_path != '' ORDER BY slot""",
                (report_id,),
            )
        ]

        prev_implemented = report_row["prev_guidance_implemented"]
        report_pdf_path = _resolve_path(db_path, report_row["pdf_path"] or "")
        report_hwpx_path = _resolve_path(db_path, report_row["hwpx_path"] or "")
        report_file_path = report_pdf_path  # CONFIRMED: K2B는 PDF만 받음(HWP/HWPX 첨부 불가)

        return K2BSubmissionData(
            site_name=site_row["name"],
            site_mgmt_no=site_row["site_mgmt_no"] or "",
            management_no=site_row["management_no"] or "",
            visit_no=report_row["visit_no"],
            guidance_date=report_row["guidance_date"],
            inspector_name=inspector_name,
            site_manager_name=site_row["manager_name"] or "",
            site_manager_phone=site_row["manager_phone"] or "",
            progress_rate=report_row["progress_rate"],
            education_count=education_count,
            distributed_material_count=material_count,
            current_process_name=report_row["current_process_name"] or "",
            special_note=report_row["special_note"] or "",
            notification_method=report_row["notification_method"] or "",
            prev_guidance_implemented=bool(prev_implemented) if prev_implemented is not None else None,
            overview_photo_paths=overview_photos,
            inspection_photo_paths=inspection_photos,
            improvement_photo_paths=improvement_photos,
            report_pdf_path=report_pdf_path,
            report_hwpx_path=report_hwpx_path,
            report_file_path=report_file_path,
        )
    finally:
        conn.close()


def list_sites(db_path: str | Path) -> list[str]:
    """12-1 DB에 등록된 현장명 목록(최신순)."""
    conn = _connect_readonly(db_path)
    try:
        return [row["name"] for row in conn.execute("SELECT name FROM site ORDER BY id DESC")]
    finally:
        conn.close()


def list_rounds(db_path: str | Path, site_name: str) -> list[int]:
    """해당 현장의 회차(visit_no) 목록(최신순)."""
    conn = _connect_readonly(db_path)
    try:
        site_row = conn.execute(
            "SELECT id FROM site WHERE name = ? ORDER BY id DESC LIMIT 1", (site_name,)
        ).fetchone()
        if site_row is None:
            return []
        return [
            row["visit_no"]
            for row in conn.execute(
                "SELECT visit_no FROM report WHERE site_id = ? ORDER BY visit_no DESC",
                (site_row["id"],),
            )
        ]
    finally:
        conn.close()
