"""디버그용 크롬을 원격 디버깅 포트와 함께 띄워두고 계속 살려둔다.

Claude가 여러 번의 별도 명령 호출에 걸쳐 이 브라우저에 CDP로 접속해서 화면을
확인/조작할 수 있게 하기 위한 용도. 로그인은 보안상 사용자가 직접 창에서 입력한다.
"""
import time

from playwright.sync_api import sync_playwright

DEBUG_PORT = 9333

with sync_playwright() as p:
    browser = p.chromium.launch(
        headless=False,
        args=[f"--remote-debugging-port={DEBUG_PORT}"],
    )
    context = browser.new_context()
    page = context.new_page()
    page.goto("https://k2b.kosha.or.kr/")
    print(f"디버그 브라우저 실행됨 (포트 {DEBUG_PORT}). 이 창은 계속 열어두세요.")
    # 계속 살아있게 대기
    while True:
        time.sleep(3600)
