"""K2B(k2b.kosha.or.kr) 브라우저 자동화.

Playwright 자체 Chromium을 사용(CDP로 기존 크롬에 붙는 방식 아님) — 로컬에서는 headed로
개발/검증하고, 나중에 서버(AWS)로 옮길 때 headless=True만 바꾸면 그대로 동작하도록 설계.

중요: 이 모듈은 **최종 저장(제출) 버튼을 누르는 코드를 포함하지 않는다.** 모든 필드
입력/사진 첨부까지만 자동화하고, 사람이 화면을 직접 확인한 뒤 수동으로 저장 버튼을
누른다. 자동 제출 기능은 다른 모든 동작이 실사용으로 검증된 뒤 가장 마지막에 추가한다
(README "개발 단계 안내" 참고).

중요(실사용 중 발견): 이 사이트는 Nexacro 기반이라 상세 모달 전체가 하나의 거대한
절대좌표(absolute positioning) 패널로 그려진다 — 일반적인 `overflow:scroll` 컨테이너가
아니라서 Playwright의 자동 "스크롤해서 보이게 하기"(`scrollIntoViewIfNeeded`)가 먹히지
않는다. 화면 아래쪽 요소(사진첨부/보고서 파일첨부 등)를 클릭하기 전에는 반드시
`_scroll_into_view()`로 실제 마우스 휠 이벤트를 보내 스크롤해야 한다 — 안 그러면
"Timeout ... waiting for event 'filechooser'"류 오류가 난다(버튼 자체가 화면 밖에 있어
클릭이 씹힘).

TODO(확인 필요, k2b_selectors.py 주석 참고):
  - 기술지도일을 다른 "달"로 바꾸는 방법(같은 달 안에서는 CONFIRMED)
  - 대형사고 위험작업이 필수인지, "해당없음"으로 건너뛸 수 있는지
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from playwright.sync_api import Page, sync_playwright

from core import k2b_selectors as sel
from core.config import K2B_LOGIN_URL

LogFn = Callable[[str], None]


def _noop_log(msg: str) -> None:
    pass


class K2BClient:
    """K2B 화면 자동화 — 로그인부터 필드 입력/사진 첨부까지. 저장은 하지 않는다."""

    def __init__(self, page: Page, log: LogFn = _noop_log):
        self.page = page
        self.log = log

    # --- 로그인/이동 ---

    def _scroll_into_view(self, locator, max_attempts: int = 20) -> None:
        """이 사이트(Nexacro)는 상세 모달 전체가 절대좌표로 배치된 하나의 거대한 패널이라
        일반적인 `overflow:scroll` 컨테이너가 아니다 -- Playwright의 자동
        `scrollIntoViewIfNeeded`가 먹히지 않아, 화면 아래쪽 요소를 클릭하기 전에는 실제
        마우스 휠 이벤트로 스크롤해야 한다(실사용 중 발견: 이 처리 없이 보고서 파일첨부
        버튼을 클릭했더니 버튼이 화면 밖에 있어 클릭이 씹히고 "filechooser" 이벤트
        타임아웃 발생). 대상 요소가 뷰포트 안에 들어올 때까지 반복 스크롤한다."""
        viewport = self.page.viewport_size or {"width": 1280, "height": 800}
        for _ in range(max_attempts):
            box = locator.bounding_box()
            if box is not None and 0 <= box["y"] <= viewport["height"] - 40:
                return
            self.page.mouse.move(viewport["width"] // 2, viewport["height"] // 2)
            self.page.mouse.wheel(0, 500)
            self.page.wait_for_timeout(150)

    def _type_into(self, locator_str: str, text: str) -> None:
        """Nexacro 커스텀 입력창은 값을 통째로 덮어쓰는 `.fill()`을 쓰면 내부 상태와
        어긋나 기존 값 뒤에 이어붙는 현상이 있었다(실사용 중 발견) — 클릭 후 전체선택+삭제로
        비우고, 실제 키보드 입력처럼 한 글자씩 입력(`press_sequentially`)한다."""
        field = self.page.locator(locator_str)
        self._scroll_into_view(field)
        field.click()
        field.press("Control+A")
        field.press("Delete")
        field.press_sequentially(text, delay=30)

    def login(self, user_id: str, password: str) -> None:
        self.log("K2B 로그인 중...")
        page = self.page
        page.goto(K2B_LOGIN_URL)
        self._type_into(sel.LOGIN_ID_INPUT, user_id)
        self._type_into(sel.LOGIN_PW_INPUT, password)
        page.get_by_text(sel.LOGIN_BUTTON_TEXT, exact=True).click()
        self.log("로그인 완료")

    def go_to_guidance_menu(self) -> None:
        """로그인 직후 대시보드("나의업무")의 "나만의 메뉴" 카드에서 "재해예방기관
        기술지도"를 바로 클릭한다(CONFIRMED, 실제 화면에서 단일 클릭으로 검색화면 도달
        확인됨) -- 로그인 후 첫 화면에서만 호출할 것(다른 화면에서는 같은 텍스트가
        사이드바 트리에도 나타나 모호할 수 있음)."""
        self.log("재해예방기관 기술지도 화면으로 이동 중...")
        self.page.get_by_text(sel.MENU_GUIDANCE_ITEM_TEXT, exact=True).click()

    # --- 검색/상세 진입 ---

    def search_site(self, site_name: str) -> None:
        self.log(f"현장명 '{site_name}' 검색 중...")
        page = self.page
        self._type_into(sel.SEARCH_SITE_NAME_INPUT, site_name)
        page.locator(sel.SEARCH_BUTTON_CONTAINER_ID).get_by_text(sel.SEARCH_BUTTON_TEXT).click()

    def select_result_row(self, site_name: str) -> None:
        """검색 결과 그리드에서 현장명 텍스트가 있는 행을 클릭해 선택한다(CONFIRMED,
        체크박스 불필요 -- 행 클릭만으로 아래 "재해예방 전문지도 기관"/"건설공사 발주자 등"
        패널에 해당 행 데이터가 로드됨을 실제 화면에서 확인)."""
        self.log(f"검색결과에서 '{site_name}' 행 선택 중...")
        self.page.get_by_text(site_name, exact=True).click()

    def open_detail(self) -> None:
        """선택된 행의 상세보기를 연다(CONFIRMED)."""
        self.log("상세보기 여는 중...")
        self.page.get_by_text(sel.DETAIL_VIEW_BUTTON_TEXT).click()

    # --- 상세 모달 입력 ---

    def add_new_round(self) -> None:
        """새 차수를 추가한다. 기술지도일이 오늘 날짜로 자동 채워지고, 이후 다른 입력
        필드들이 활성화된다(현장에 등록된 차수가 없을 때 실기록으로 확인됨)."""
        self.log("차수 추가 중...")
        self.page.locator(sel.ADD_ROUND_BUTTON_ID).get_by_text(sel.ADD_ROUND_BUTTON_TEXT).click()

    def set_guidance_date(self, day: int) -> None:
        """기술지도일을 캘린더 팝업에서 선택한다. 현재 팝업에 표시된 달의 `day`일을 클릭한다.

        주의(TODO): 목표 날짜가 현재 표시된 달과 다른 달이면 이 메서드로는 못 바꾼다(월
        이동 화살표 셀렉터 미검증). "+추가" 시 자동으로 오늘 날짜가 들어가므로, 오늘과
        같은 달의 날짜를 바꾸는 경우에만 안전하게 쓸 것. 또한 한 자리 숫자(1~9일)는
        팝업에 표시되는 다음달 잔여일과 텍스트가 겹칠 수 있어 `.first`로 첫 번째 일치
        항목(현재 달 쪽이 DOM상 먼저 나옴, 실기록으로 확인)을 클릭한다."""
        self.log(f"기술지도일 {day}일로 변경 중...")
        page = self.page
        page.locator(sel.GUIDANCE_DATE_CALENDAR_BUTTON_ID).click()
        page.get_by_text(str(day), exact=True).first.click()

    def fill_progress_rate(self, percent: int) -> None:
        self.log(f"공정률 {percent}% 입력 중...")
        self._type_into(sel.PROGRESS_RATE_INPUT_ID, str(percent))

    def fill_site_manager_name(self, name: str) -> None:
        self.log(f"현장책임자명 '{name}' 입력 중...")
        self._type_into(sel.SITE_MANAGER_NAME_INPUT_ID, name)

    def fill_site_manager_phone(self, phone: str) -> None:
        """현장책임자 연락처를 입력한다. 마스크 입력 필드라 하이픈 유무와 무관하게
        숫자만 뽑아서 순서대로 입력하면 "010-1234-5678" 형태로 자동 포맷된다(CONFIRMED).
        보고서에 "031-757-1930"/"0317571930" 두 표기가 섞여 나올 수 있어 숫자만 추출한다."""
        digits = "".join(ch for ch in phone if ch.isdigit())
        if not digits:
            return
        self.log(f"현장책임자 연락처 입력 중... ({digits})")
        self._type_into(sel.SITE_MANAGER_PHONE_INPUT_ID, digits)

    def fill_special_note(self, text: str) -> None:
        self.log("특이사항 입력 중...")
        self._type_into(sel.SPECIAL_NOTE_INPUT_ID, text)

    # 점검자(INSCTR_NM)는 CONFIRMED readonly -- 로그인 계정 이름이 자동 적용되고 화면에서
    # 수정 불가능하다(k2b_selectors.INSPECTOR_NAME_INPUT_ID 주석 참고). 그래서 이 클래스에
    # 점검자를 채우는 메서드가 의도적으로 없다 -- 다른 담당요원 이름으로 제출하려면 그
    # 담당요원 계정으로 로그인해야 하는지 고객에게 확인 필요(TODO, 보류 중).

    def set_scaffold_usage(self, used: bool, types: list[str] | None = None) -> None:
        """비계사용현황을 설정한다. used=True면 "사용" 선택 후 types(예: ["강관비계"])의
        비계종류 체크박스도 켠다. used=False면 "미사용"만 선택(비계종류는 자동 비활성화됨,
        CONFIRMED)."""
        page = self.page
        if used:
            self.log("비계사용현황 '사용'으로 설정 중...")
            radio = page.get_by_text(sel.SCAFFOLD_USAGE_RADIO_GROUP_TEXT["사용"], exact=True)
            self._scroll_into_view(radio)
            radio.click()
            for t in types or []:
                checkbox_id = sel.SCAFFOLD_TYPE_CHECKBOX_IDS.get(t)
                if checkbox_id is None:
                    raise ValueError(f"알 수 없는 비계종류: {t}")
                checkbox = page.locator(checkbox_id)
                self._scroll_into_view(checkbox)
                checkbox.click()
        else:
            self.log("비계사용현황 '미사용'으로 설정 중...")
            radio = page.get_by_text(sel.SCAFFOLD_USAGE_RADIO_GROUP_TEXT["미사용"], exact=True)
            self._scroll_into_view(radio)
            radio.click()

    def select_current_process(self, process_name: str) -> None:
        self.log(f"현재 작업공정 '{process_name}' 선택 중...")
        page = self.page
        dropdown = page.locator(sel.CURRENT_PROCESS_DROPDOWN_ID)
        self._scroll_into_view(dropdown)
        dropdown.click()
        page.get_by_text(process_name).click()

    def check_notification_method(self, method: str) -> None:
        """method: '직접전달' | '등기우편' | '전자우편' | '모바일' | '기타'"""
        checkbox_id = sel.NOTIFICATION_METHOD_CHECKBOX_IDS.get(method)
        if checkbox_id is None:
            raise ValueError(f"알 수 없는 통보방법: {method}")
        self.log(f"통보방법 '{method}' 체크 중...")
        checkbox = self.page.locator(checkbox_id)
        self._scroll_into_view(checkbox)
        checkbox.click()

    def check_prev_guidance_implemented(self, status: str) -> None:
        """status: '이행' | '불이행' | '해당없음' (세 옵션 모두 실제 클릭으로 CONFIRMED)"""
        checkbox_id = sel.PREV_GUIDANCE_IMPLEMENTED_CHECKBOX_IDS.get(status)
        if checkbox_id is None:
            raise ValueError(f"알 수 없는 이행여부: {status}")
        self.log(f"이전 기술지도 이행여부 '{status}' 체크 중...")
        checkbox = self.page.locator(checkbox_id)
        self._scroll_into_view(checkbox)
        checkbox.click()

    def attach_photos(self, category: str, file_paths: list[str | Path]) -> None:
        """category: '현장전경' | '현장점검' | '현장개선'

        사진첨부 버튼 클릭 -> 파일 선택창(file chooser)에서 다중 파일 선택(CONFIRMED,
        실제 파일 업로드까지 end-to-end 검증됨)."""
        button_id = sel.PHOTO_ATTACH_BUTTON_IDS.get(category)
        if button_id is None:
            raise ValueError(f"알 수 없는 사진 카테고리: {category}")
        if not file_paths:
            return
        self.log(f"{category} 사진 {len(file_paths)}장 첨부 중...")
        page = self.page
        button = page.locator(button_id).get_by_text(sel.PHOTO_ATTACH_BUTTON_TEXT)
        self._scroll_into_view(button)
        with page.expect_file_chooser() as fc_info:
            button.click()
        file_chooser = fc_info.value
        file_chooser.set_files([str(p) for p in file_paths])

    def add_major_hazard_work(self, option: str) -> None:
        """"대형사고 위험작업"에 새 행을 추가하고 종류를 선택한다(CONFIRMED 흐름).

        option은 k2b_selectors.MAJOR_HAZARD_WORK_OPTIONS 중 하나. 주의(TODO): "선택"
        텍스트로 새로 생긴 행의 드롭다운 셀을 찾는데, 화면에 "선택"이라는 텍스트가 이
        영역 말고 다른 곳에도 있으면 잘못된 요소를 클릭할 위험이 있다 -- 이 모달 안에서는
        실사용으로 문제 없었으나 다른 화면 상태에서는 재검증 필요."""
        if option not in sel.MAJOR_HAZARD_WORK_OPTIONS:
            raise ValueError(f"알 수 없는 대형사고 위험작업 종류: {option}")
        self.log(f"대형사고 위험작업 '{option}' 추가 중...")
        page = self.page
        add_button = page.locator(sel.MAJOR_HAZARD_WORK_ADD_BUTTON_ID).get_by_text("추가")
        self._scroll_into_view(add_button)
        add_button.click()
        select_cell = page.get_by_text("선택", exact=True).first
        self._scroll_into_view(select_cell)
        select_cell.click()
        select_cell.click()
        page.get_by_text(option, exact=True).click()

    def attach_report_file(self, file_path: str | Path) -> None:
        """12-1에서 생성된 실제 결과보고서(PDF/hwpx) 파일을 "보고서" 섹션에 첨부한다.

        주의(CONFIRMED, 실제 화면에서 확인): 기술지도일 이후 7일이 지나면 보고서 수정이
        불가능해진다 -- 제출 자동화는 이 기한 안에 실행되어야 한다."""
        self.log(f"보고서 파일 첨부 중: {file_path}")
        page = self.page
        button = page.locator(sel.REPORT_FILE_ATTACH_BUTTON_ID).get_by_text(sel.REPORT_FILE_ATTACH_BUTTON_TEXT)
        self._scroll_into_view(button)
        with page.expect_file_chooser() as fc_info:
            button.click()
        file_chooser = fc_info.value
        file_chooser.set_files(str(file_path))

    # 최종 저장(제출) 메서드는 의도적으로 아직 없음. README "개발 단계 안내" 참고.


def open_browser(headless: bool = False):
    """Playwright 컨텍스트 매니저를 직접 열어야 할 때 쓰는 헬퍼.

    사용 예:
        with open_browser() as (playwright, browser, page):
            client = K2BClient(page, log=print)
            client.login(user_id, password)
            ...
    """
    playwright = sync_playwright().start()
    browser = playwright.chromium.launch(headless=headless)
    context = browser.new_context()
    page = context.new_page()
    return playwright, browser, page
