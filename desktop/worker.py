# -*- coding: utf-8 -*-
"""K2B 자동입력을 백그라운드 스레드에서 실행하는 워커 (11번 프로젝트의 workers/ 패턴 참고).

Playwright(sync API)를 Qt 메인 스레드에서 직접 돌리면 UI가 멈추므로 QThread 안에서 실행한다.
저장(제출) 버튼은 절대 누르지 않는다 -- 다 채운 뒤 브라우저를 열어둔 채로 끝나고, 사람이
직접 확인 후 수동으로 저장하거나 창을 닫으면 된다."""
from __future__ import annotations

from PyQt6.QtCore import QThread, pyqtSignal

from core.db_reader import K2BSubmissionData
from core.k2b_client import K2BClient, open_browser


class K2BFillWorker(QThread):
    log_message = pyqtSignal(str)
    finished_ok = pyqtSignal()
    failed = pyqtSignal(str)

    def __init__(self, user_id: str, password: str, data: K2BSubmissionData, is_new_round: bool):
        super().__init__()
        self.user_id = user_id
        self.password = password
        self.data = data
        self.is_new_round = is_new_round

    def run(self) -> None:
        playwright = browser = None
        try:
            playwright, browser, page = open_browser(headless=False)
            client = K2BClient(page, log=self.log_message.emit)
            d = self.data

            client.login(self.user_id, self.password)
            client.go_to_guidance_menu()
            client.search_site(d.site_name)
            client.select_result_row(d.site_name)
            client.open_detail()

            if self.is_new_round:
                client.add_new_round()

            if d.progress_rate is not None:
                client.fill_progress_rate(d.progress_rate)
            if d.site_manager_name:
                client.fill_site_manager_name(d.site_manager_name)
            if d.site_manager_phone:
                client.fill_site_manager_phone(d.site_manager_phone)
            if d.special_note:
                client.fill_special_note(d.special_note)
            if d.current_process_name:
                client.select_current_process(d.current_process_name)
            if d.notification_method:
                client.check_notification_method(d.notification_method)
            if d.prev_guidance_implemented is not None:
                status = "이행" if d.prev_guidance_implemented else "불이행"
                client.check_prev_guidance_implemented(status)
            # 점검자는 로그인 계정 이름으로 고정되는 readonly 필드라 자동입력 안 함
            # -- 작업내용.md "GUI TODO: 로그인 계정 관리 화면" 참고(보류 중).

            if d.overview_photo_paths:
                client.attach_photos("현장전경", d.overview_photo_paths)
            if d.inspection_photo_paths:
                client.attach_photos("현장점검", d.inspection_photo_paths)
            if d.report_file_path:
                client.attach_report_file(d.report_file_path)

            self.log_message.emit("자동 입력 완료. 브라우저에서 직접 화면을 확인한 뒤, "
                                   "필요하면 수동으로 저장 버튼을 눌러주세요.")
            self.log_message.emit("이 창은 자동으로 닫히지 않습니다 -- 확인 후 직접 닫으세요.")
            self.finished_ok.emit()

            # 사용자가 브라우저에서 직접 확인/조작할 시간을 준다. 창을 닫을 때까지 대기.
            while browser.is_connected():
                self.msleep(1000)
        except Exception as e:  # noqa: BLE001 -- 워커 스레드 최상위, UI로 실패를 알려야 함
            self.failed.emit(str(e))
        finally:
            try:
                if browser is not None and browser.is_connected():
                    browser.close()
            except Exception:
                pass
            if playwright is not None:
                playwright.stop()
