"""K2B 로그인 정보 암호화 저장/조회 — 담당요원별로 여러 계정을 등록할 수 있다.

Windows Credential Manager(keyring 백엔드)에 저장한다 — 평문 파일에 직접 쓰지 않고
OS 수준 암호화 저장소를 사용하므로 자체 암호화 키를 관리할 필요가 없다.

배경: K2B의 "점검자" 필드는 로그인한 계정 이름으로 고정되는 readonly 필드였다(실사용
확인, 작업내용.md 참고). 즉 12-1 DB의 담당요원(예: "현수아")과 같은 이름으로 점검자를
제출하려면 그 담당요원 명의의 K2B 계정으로 로그인해야 한다 — 그래서 계정을 "담당요원
이름"으로 구분해 여러 개 저장한다. (담당요원별 K2B 계정이 실제로 존재하는지는 아직
고객 확인 전 — 그 전까지는 등록된 계정이 하나뿐이어도 무방하게 동작한다.)

CLI로 직접 실행하면 터미널에서만 아이디/비밀번호를 입력받는다(대화창에는 절대 노출 안 됨).
    python -m core.credentials set <담당요원이름>
    python -m core.credentials list
    python -m core.credentials show <담당요원이름>
    python -m core.credentials delete <담당요원이름>
"""

from __future__ import annotations

import getpass
import json
import sys

import keyring

SERVICE_NAME = "k2b_kosha_auto_submit"
_INDEX_KEY = "__account_index__"


def _load_index() -> list[str]:
    raw = keyring.get_password(SERVICE_NAME, _INDEX_KEY)
    if not raw:
        return []
    try:
        return json.loads(raw)
    except ValueError:
        return []


def _save_index(names: list[str]) -> None:
    keyring.set_password(SERVICE_NAME, _INDEX_KEY, json.dumps(names, ensure_ascii=False))


def list_accounts() -> list[str]:
    """등록된 담당요원 이름 목록."""
    return _load_index()


def set_account(staff_name: str, user_id: str, password: str) -> None:
    keyring.set_password(SERVICE_NAME, f"{staff_name}::id", user_id)
    keyring.set_password(SERVICE_NAME, f"{staff_name}::password", password)
    names = _load_index()
    if staff_name not in names:
        names.append(staff_name)
        _save_index(names)


def get_account(staff_name: str) -> tuple[str, str] | None:
    user_id = keyring.get_password(SERVICE_NAME, f"{staff_name}::id")
    password = keyring.get_password(SERVICE_NAME, f"{staff_name}::password")
    if not user_id or not password:
        return None
    return user_id, password


def delete_account(staff_name: str) -> None:
    for suffix in ("id", "password"):
        try:
            keyring.delete_password(SERVICE_NAME, f"{staff_name}::{suffix}")
        except keyring.errors.PasswordDeleteError:
            pass
    names = _load_index()
    if staff_name in names:
        names.remove(staff_name)
        _save_index(names)


def find_account_for_inspector(inspector_name: str) -> tuple[str, str] | None:
    """12-1 DB의 담당요원 이름과 정확히 일치하는 등록 계정이 있으면 반환."""
    if inspector_name in list_accounts():
        return get_account(inspector_name)
    return None


def _cli() -> None:
    if len(sys.argv) < 2:
        print("사용법: python -m core.credentials [set|show|delete|list] <담당요원이름>")
        return

    action = sys.argv[1]
    if action == "list":
        names = list_accounts()
        if names:
            print("등록된 계정:", ", ".join(names))
        else:
            print("등록된 계정 없음")
        return

    if len(sys.argv) < 3:
        print("담당요원 이름을 지정하세요. 예: python -m core.credentials set 현수아")
        return
    staff_name = sys.argv[2]

    if action == "set":
        user_id = input(f"'{staff_name}'의 K2B 아이디: ").strip()
        password = getpass.getpass(f"'{staff_name}'의 K2B 비밀번호: ")
        set_account(staff_name, user_id, password)
        print("저장 완료 (Windows 자격 증명 관리자에 암호화 저장됨)")
    elif action == "show":
        creds = get_account(staff_name)
        if creds:
            print(f"'{staff_name}' 저장된 아이디: {creds[0]} (비밀번호는 표시하지 않음)")
        else:
            print(f"'{staff_name}' 계정 없음")
    elif action == "delete":
        delete_account(staff_name)
        print("삭제 완료")
    else:
        print("사용법: python -m core.credentials [set|show|delete|list] <담당요원이름>")


if __name__ == "__main__":
    _cli()
