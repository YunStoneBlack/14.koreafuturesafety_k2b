"""확인된 셀렉터로 실제 자동화가 동작하는지 테스트하는 스크립트.

사전 준비:
    venv\\Scripts\\python.exe -m core.credentials set <담당요원이름>   # 최초 1회, K2B 계정 암호화 저장

실행:
    venv\\Scripts\\python.exe run_test_fill.py "현장명" "담당요원이름"

로그인 -> 메뉴 이동 -> 현장 검색 -> 행 선택 -> 상세보기 -> 차수 추가 -> 공정률/현재작업공정/
통보방법/이전기술지도 이행여부까지 자동 입력하고 멈춘다. **저장 버튼은 누르지 않는다** —
직접 화면 확인 후 그냥 브라우저 창을 닫으면 된다.

주의: 실제 존재하는(실사용 중인) 현장명으로 테스트하면 "차수 추가"가 그 현장에 새 회차를
하나 만든다(저장 전까지는 실제 DB에 반영 안 됨). 절대 화면에서 직접 저장 버튼을 누르지
말 것 -- 실제 제출 데이터가 오염될 수 있다.
"""

from __future__ import annotations

import sys

from core.credentials import get_account, list_accounts
from core.k2b_client import K2BClient, open_browser


def main() -> None:
    site_name = sys.argv[1] if len(sys.argv) > 1 else input("검색할 현장명: ").strip()
    if len(sys.argv) > 2:
        staff_name = sys.argv[2]
    else:
        names = list_accounts()
        staff_name = names[0] if len(names) == 1 else input("로그인할 담당요원 이름: ").strip()

    creds = get_account(staff_name)
    if creds is None:
        print(f"'{staff_name}' 계정이 없습니다. 먼저 실행하세요: python -m core.credentials set {staff_name}")
        return
    user_id, password = creds

    playwright, browser, page = open_browser(headless=False)
    client = K2BClient(page, log=print)
    try:
        client.login(user_id, password)
        client.go_to_guidance_menu()
        client.search_site(site_name)
        client.select_result_row(site_name)
        client.open_detail()
        client.add_new_round()
        client.fill_progress_rate(70)
        client.select_current_process("굴착공사")
        client.check_notification_method("전자우편")
        client.check_prev_guidance_implemented("불이행")

        print("\n여기까지 자동 입력 완료. 브라우저에서 직접 화면을 확인하세요.")
        print("저장 버튼은 자동으로 누르지 않습니다. 확인 후 Enter를 누르면 브라우저를 닫습니다.")
        input()
    finally:
        browser.close()
        playwright.stop()


if __name__ == "__main__":
    main()
