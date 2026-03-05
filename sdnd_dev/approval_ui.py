"""
承認UI
Reviewerが承認したセッションをあなたが最終確認するためのCLIインターフェース

使い方：
  python sdnd_dev/approval_ui.py
  python sdnd_dev/approval_ui.py --session sessions/dev_scenario/xxx.json
"""

from __future__ import annotations

import json
import argparse
from pathlib import Path

SESSION_DIR = Path("sessions/dev_scenario")


def show_session(session: dict):
    """セッション内容をコンパクトに表示"""
    print(f"\n{'='*60}")
    print(f"タスク  : {session.get('task')}")
    print(f"結果    : {session.get('result')}")
    print(f"ターン数: {len(session.get('turns', []))}")
    print(f"{'='*60}")

    # 最終ターンのコードと Reviewer コメントを表示
    turns = session.get("turns", [])
    if turns:
        last = turns[-1]
        print(f"\n[最終コード]\n{last.get('code', '（なし）')}")
        print(f"\n[Reviewerコメント]\n{last.get('reviewer', '（なし）')}")
        print(f"\n[実行結果]\n{last.get('exec_result', {}).get('stdout', '（なし）')}")


def prompt_approval() -> tuple[str, str]:
    """
    承認・却下・差し戻しを入力させる
    Returns: (action, comment)
    """
    print("\n" + "-"*60)
    print("  [A] 承認（採用）")
    print("  [R] 却下（不採用）")
    print("  [S] 差し戻し（コメント付き）")
    print("-"*60)

    while True:
        choice = input("選択 > ").strip().upper()
        if choice == "A":
            return "approved", ""
        elif choice == "R":
            return "rejected", ""
        elif choice == "S":
            comment = input("差し戻しコメント > ").strip()
            return "sendback", comment
        else:
            print("A / R / S を入力してください")


def run_approval_ui(session_path: Path | None = None):
    """未承認セッションを順番に表示して承認・却下させる"""

    # 対象セッションを取得
    if session_path:
        paths = [session_path]
    else:
        # 未承認（human_approval が pending）のものを抽出
        paths = sorted(SESSION_DIR.glob("*.json"), key=lambda p: p.stat().st_mtime)
        paths = [p for p in paths if _needs_approval(p)]

    if not paths:
        print("承認待ちのセッションはありません。")
        return

    print(f"\n承認待ち: {len(paths)} 件")

    for path in paths:
        session = json.loads(path.read_text(encoding="utf-8"))
        show_session(session)

        action, comment = prompt_approval()

        # セッションに結果を記録
        session["human_approval"] = {
            "action": action,
            "comment": comment,
        }
        path.write_text(json.dumps(session, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"→ {action} を記録しました: {path.name}")


def _needs_approval(path: Path) -> bool:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        approval = data.get("human_approval", {})
        return approval.get("action") == "pending" or "human_approval" not in data
    except Exception:
        return False


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--session", type=Path, help="特定セッションのパス")
    args = parser.parse_args()
    run_approval_ui(session_path=args.session)
