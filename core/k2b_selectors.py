"""K2B(k2b.kosha.or.kr) 실제 화면 셀렉터.

`record_flow.py`(Playwright codegen) 녹화 결과(`data/recorded_flow.py`)에서 추출.
이 사이트는 Nexacro 기반이라 요소 id가 `mainframe_VFrameSet_MainFrame_<모듈코드>_form_tab_..._<필드코드>`
패턴으로 비교적 안정적이다. 모듈코드 `103015010`=목록화면, `EBP00130_P01`=상세입력 모달.

각 상수 옆에 확인 상태를 표시:
  CONFIRMED - 실제 녹화에서 동작 확인됨
  GUESS     - 다른 필드와의 패턴 유추, 실사용 전 검증 필요
  TODO      - 아직 모름, 추가 확인 필요
"""

from __future__ import annotations

# --- 로그인 (CONFIRMED) ---
LOGIN_ID_INPUT = "#mainframe_VFrameSet_LoginFrame_form_div_Login_div_box_edt_mber_id_input"
LOGIN_PW_INPUT = "#mainframe_VFrameSet_LoginFrame_form_div_Login_div_box_edt_password_input"
LOGIN_BUTTON_TEXT = "로그인"  # get_by_text(..., exact=True)

# --- 메뉴 이동 (CONFIRMED) ---
MENU_GUIDANCE_SUPPORT_TEXT = "건설재해예방전문기관 기술지원"
MENU_TREE_ITEM_ID = (
    "#mainframe_VFrameSet_MainFrame_form_div_Form_div_Left_grd_Menu_body_gridrow_1_cell_1_1_controltreeTextBoxElement"
)
MENU_GUIDANCE_ITEM_TEXT = "재해예방기관 기술지도"

# --- 검색 화면 (CONFIRMED, 모듈코드 103015010) ---
SEARCH_SITE_NAME_INPUT = (
    "#mainframe_VFrameSet_MainFrame_form_div_Form_div_Work_103015010_div_Work_div_Search_edt_ENTRPS_NM_input"
)
SEARCH_BUTTON_CONTAINER_ID = (
    "#mainframe_VFrameSet_MainFrame_form_div_Form_div_Work_103015010_div_Work_div_Search_btn_SearchTextBoxElement"
)
SEARCH_BUTTON_TEXT = "조회"

# 결과 행 선택 - CONFIRMED: 체크박스 없이 현장명 텍스트가 있는 행을 그냥 클릭하면 선택되고
# (218건 중 특정 행 클릭 -> 아래 패널에 해당 데이터 로드 확인됨) 상세보기가 그 행을 연다.
DETAIL_VIEW_BUTTON_TEXT = "상세보기"  # CONFIRMED

# --- 상세 모달 (CONFIRMED, 모듈코드 EBP00130_P01) ---
_MODAL_PREFIX = "#mainframe_VFrameSet_MainFrame_EBP00130_P01_form_tab_Main_tabpage1"

ADD_ROUND_BUTTON_ID = f"{_MODAL_PREFIX}_btn_AddTextBoxElement"
ADD_ROUND_BUTTON_TEXT = "추가"

# 기술지도일 - "+추가" 클릭 시 오늘 날짜로 자동 채워짐(CONFIRMED). 다른 날짜로 바꾸는
# 방법도 CONFIRMED: 달력 아이콘 클릭 -> 팝업(해당 월 달력, "◀ YYYY.MM ▶" 헤더 + 날짜 그리드)
# -> 원하는 날짜 텍스트 클릭 -> 필드에 반영됨(실기록: 09-09 -> 09-20 변경 후 원복까지 검증).
# 주의(TODO): 팝업의 날짜 셀은 get_by_text(str(day))로 찾는데, 이전달/다음달 잔여일도 같은
# 텍스트(예: "1"~"10")를 가질 수 있어 모호할 수 있다 -- 목표 날짜가 팝업에 보이는 달과
# 다르면 ◀/▶로 먼저 월을 이동해야 하고, 한 자리 숫자 날짜는 다음달 잔여일과 겹칠 위험이
# 있으니 실제 구현 시 좌표 기반 클릭이나 셀의 회색/검정 텍스트색 구분으로 명확히 해야 함.
GUIDANCE_DATE_CALENDAR_BUTTON_ID = f"{_MODAL_PREFIX}_cal_TCHGUD_YMD_dropbuttonAlignImageElement"
GUIDANCE_DATE_CALENDAR_PREV_MONTH_TEXT = "◀"  # GUESS(화면상 화살표, 정확한 글자/aria 확인 필요)
GUIDANCE_DATE_CALENDAR_NEXT_MONTH_TEXT = "▶"  # GUESS
GUIDANCE_DATE_INPUT_ID = None  # TODO: 달력 텍스트 입력 부분(직접 타이핑용)의 실제 id 확인 필요

PROGRESS_RATE_INPUT_ID = f"{_MODAL_PREFIX}_edt_PROCS_RAT_CVALUE_input"  # CONFIRMED, .fill("70") 동작

# 점검자 - CONFIRMED readonly (입력 시도해도 값이 안 바뀜, is_editable()=False, readonly
# 속성 존재). 로그인한 K2B 계정의 실명이 자동으로 들어가는 것으로 추정(기존 차수마다 값이
# 다른 건 그 회차를 저장할 때 로그인했던 계정이 달랐기 때문으로 보임 -- 검증은 아직 TODO,
# 고객에게 "담당요원별로 K2B 계정이 따로 있는지" 확인 필요). 그때까지 이 필드는 채우려
# 시도하지 않는다.
INSPECTOR_NAME_INPUT_ID = f"{_MODAL_PREFIX}_edt_INSCTR_NM_input"  # CONFIRMED readonly -- 채우지 말 것

SITE_MANAGER_NAME_INPUT_ID = f"{_MODAL_PREFIX}_edt_SPT_RSPNBER_NM_input"  # CONFIRMED, 편집 가능
SPECIAL_NOTE_INPUT_ID = f"{_MODAL_PREFIX}_edt_PARTCLR_MATTER_CN_input"  # CONFIRMED (특이사항)
GUIDANCE_COUNT_INPUT_ID = f"{_MODAL_PREFIX}_edt_CCH_NOCS_input"  # 지도건수, id만 확인(TODO: 편집 가능 여부 미검증)
EDUCATION_COUNT_INPUT_ID = f"{_MODAL_PREFIX}_edt_PREARNGE_NMPR_CNT_input"  # 교육인원, id만 확인
DISTRIBUTED_MATERIAL_COUNT_INPUT_ID = f"{_MODAL_PREFIX}_edt_WDTB_DATA_NOCS_input"  # 배포자료건수, id만 확인

# 현장책임자 연락처 - CONFIRMED. 겉보기엔 3칸(지역-국번-번호)처럼 보이지만 실제로는
# **마스크 입력(msk_) 단일 필드 하나**다. 빈 값일 때 placeholder가 "___-____-____"로
# 표시돼 3칸처럼 보였을 뿐. 숫자만 순서대로 press_sequentially하면 마스크가 자동으로
# 하이픈을 넣어준다(실기록: "01099998888" 입력 -> "010-9999-8888"로 정확히 반영, 원복 완료).
SITE_MANAGER_PHONE_INPUT_ID = f"{_MODAL_PREFIX}_msk_SPT_RSPNBER_TELNO_input"

CURRENT_PROCESS_DROPDOWN_ID = f"{_MODAL_PREFIX}_cbo_NOW_OPERT_PROCS_dropbutton > div"  # CONFIRMED
# 옵션 선택은 드롭다운 클릭 후 get_by_text(옵션명)으로 선택 (CONFIRMED, 예: "굴착공사")
CURRENT_PROCESS_OPTIONS = [
    "가설공사", "굴착공사", "골조공사", "마감공사", "부대토목공사", "실내인테리어공사", "기타공사",
]  # CONFIRMED (드롭다운 전체 목록 실화면 확인)

# 비계사용현황/비계종류 - CONFIRMED (실제 라디오/체크박스 토글해 동작 확인 후 원복함).
# 특이사항: 이 두 필드는 상세모달(EBP00130_P01)이 아니라 뒤에 깔린 검색화면 모듈
# (103015010) DOM에 속해 있다(id 프리픽스가 다름) -- 화면상 모달 위에 겹쳐 보일 뿐 실제
# 컨테이너가 다르므로 _MODAL_PREFIX를 안 쓰고 별도 상수로 둔다.
# "사용"/"미사용" 라디오는 그룹 전체가 같은 id(rdo_SCFDG_USE_YN_item)로 묶여 개별 id가
# 없어 텍스트 클릭으로 처리해야 한다(GUIDANCE_DATE 등과 달리 id 지정 불가).
SCAFFOLD_USAGE_RADIO_GROUP_TEXT = {"사용": "사용", "미사용": "미사용"}  # get_by_text(exact=True)로 클릭
SCAFFOLD_TYPE_CHECKBOX_IDS = {
    "강관비계": "#mainframe_VFrameSet_MainFrame_form_div_Form_div_Work_103015010_div_Work_CURR_SCFDG_INSTL_STLE_CMMN_CD_5",
    "시스템비계": "#mainframe_VFrameSet_MainFrame_form_div_Form_div_Work_103015010_div_Work_CURR_SCFDG_INSTL_STLE_CMMN_CD_6",
}  # CONFIRMED, "사용" 선택 후에만 클릭 가능(미사용 상태에서는 비활성화됨)

# 현장책임자 등 통보방법 체크박스 - 전체 CONFIRMED: 003=전자우편은 실제 저장된 데이터
# (마산3리 2회차)로, 001/002/004/005는 각 라벨 옆 요소의 실제 id를 직접 조회해 확인.
NOTIFICATION_METHOD_CHECKBOX_IDS = {
    "직접전달": f"{_MODAL_PREFIX}_chk01_001_chkimg > div",  # CONFIRMED
    "등기우편": f"{_MODAL_PREFIX}_chk01_002_chkimg > div",  # CONFIRMED
    "전자우편": f"{_MODAL_PREFIX}_chk01_003_chkimg > div",  # CONFIRMED
    "모바일": f"{_MODAL_PREFIX}_chk01_004_chkimg > div",  # CONFIRMED
    "기타": f"{_MODAL_PREFIX}_chk01_005_chkimg > div",  # CONFIRMED
}

# 이전 기술지도 이행여부 체크박스 - 전체 CONFIRMED. 코드 체계가 대칭적(Y/N)이 아니라
# 0/1/N임을 DOM 전체 id 스캔으로 먼저 찾고(chk02_0/chk02_1/chk02_N 세 개만 존재), 각각
# 실제로 클릭해 화면에서 "해당없음"/"불이행"으로 정확히 토글되는 것까지 검증 후 원복함.
PREV_GUIDANCE_IMPLEMENTED_CHECKBOX_IDS = {
    "이행": f"{_MODAL_PREFIX}_chk02_1_chkimg > div",  # CONFIRMED
    "불이행": f"{_MODAL_PREFIX}_chk02_N_chkimg > div",  # CONFIRMED
    "해당없음": f"{_MODAL_PREFIX}_chk02_0_chkimg > div",  # CONFIRMED
}

# 사진첨부 버튼 3종 - CONFIRMED (실제 화면 스크롤로 순서/섹션 확인 완료):
# imgAdd=현장전경, imgAdd2=현장점검, imgAdd3=현장개선.
PHOTO_ATTACH_BUTTON_IDS = {
    "현장전경": f"{_MODAL_PREFIX}_btn_imgAddTextBoxElement",  # CONFIRMED
    "현장점검": f"{_MODAL_PREFIX}_btn_imgAdd2TextBoxElement",  # CONFIRMED
    "현장개선": f"{_MODAL_PREFIX}_btn_imgAdd3TextBoxElement",  # CONFIRMED
}
PHOTO_ATTACH_BUTTON_TEXT = "사진첨부"

# 대형사고 위험작업 - CONFIRMED 전체 흐름 (추가 -> 드롭다운 선택 -> 제거까지 실제 테스트).
# "추가" 클릭 시 새 행 생성(업무영역/발생형태/예정시기 기본값 자동, "대형사고 위험작업"
# 칸은 "선택" 드롭다운). 드롭다운 클릭하면 콤보박스로 바뀌고, 옵션 5종(CONFIRMED):
#   비계 설치 및 해체
#   거푸집동바리(작업발판 일체형 거푸집 포함) 설치 및 해체
#   흙막이지보공(내공단면적 2㎡미만 터널 지보공 포함) 설치 및 해체
#   기타 추락위험 장소·작업(달비계 작업, 지붕공사 등)
#   밀폐공간 및 화재·폭발
# 필수 여부/"해당없음" 체크로 건너뛸 수 있는지는 아직 TODO(저장을 안 눌러서 검증 안 됨).
MAJOR_HAZARD_WORK_ADD_BUTTON_ID = f"{_MODAL_PREFIX}_div_Cnstrc_btn_AddTextBoxElement"  # CONFIRMED
MAJOR_HAZARD_WORK_REMOVE_BUTTON_TEXT = "제거"  # CONFIRMED (같은 영역 내 버튼, 텍스트로 클릭)
MAJOR_HAZARD_WORK_NA_CHECKBOX_TEXT = "해당없음"  # 존재만 CONFIRMED, 동작은 TODO
MAJOR_HAZARD_WORK_OPTIONS = [
    "비계 설치 및 해체",
    "거푸집동바리(작업발판 일체형 거푸집 포함) 설치 및 해체",
    "흙막이지보공(내공단면적 2㎡미만 터널 지보공 포함) 설치 및 해체",
    "기타 추락위험 장소·작업(달비계 작업, 지붕공사 등)",
    "밀폐공간 및 화재·폭발",
]  # CONFIRMED

# 보고서 파일첨부 - CONFIRMED. "보고서" 섹션(맨 아래, 현장개선 사진 다음)의 파일첨부 버튼.
# 12-1에서 생성된 실제 결과보고서 파일이 여기 들어간다.
# 형식 CONFIRMED: HWP/HWPX는 첨부 자체가 안 되고 **PDF만 가능**(실사용 중 확인) -- 더 이상
# "미확정" 아님, report_file_path는 항상 PDF를 쓴다(db_reader.py 참고).
# 실제 데이터로 확인된 제약: "기술지도일 이후 7일 초과 시 보고서 수정 불가" -- 자동화
# 스케줄링 시 이 기한 안에 제출해야 함.
REPORT_FILE_ATTACH_BUTTON_ID = f"{_MODAL_PREFIX}_btn_etcAddTextBoxElement"  # CONFIRMED
REPORT_FILE_ATTACH_BUTTON_TEXT = "파일첨부"
# "보고서 수정가능 기한" 표시 필드 -- CONFIRMED(MDFCN_POSBL_YMD = 수정가능일). 이 날짜가
# 지나면 REPORT_FILE_ATTACH_BUTTON이 비활성화돼 클릭해도 반응이 없다(실사용 중 재현:
# 기존 차수를 그대로 열어 편집했더니 기한이 지나있어 "파일첨부"를 눌러도 파일선택창이
# 전혀 안 뜨고 filechooser 이벤트 타임아웃만 남 -- 스크롤 문제가 아니었음).
REPORT_MODIFIABLE_UNTIL_INPUT_ID = f"{_MODAL_PREFIX}_cal_MDFCN_POSBL_YMD_calendaredit_input"

# 최종 저장(=제출) - 의도적으로 이 파일에 셀렉터를 넣지 않는다.
# 모든 기능이 검증된 뒤 마지막 단계에서만 추가한다 (README "개발 단계 안내" 참고).
SAVE_SUBMIT_BUTTON_ID = None  # 의도적 미구현
