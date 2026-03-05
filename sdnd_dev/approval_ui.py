"""
承認UI
Reviewerが承認したセッションをあなたが最終確認するためのCLIインターフェース

使い方：
  python sdnd_dev/approval_ui.py
  python sdnd_dev/approval_ui.py --session sessions/dev_scenario/xxx.json
"""

from __future__ import annotations

import csv
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


def show_summary():
    """承認済みセッション数と平均ターン数を表示"""
    paths = sorted(SESSION_DIR.glob("*.json"))
    if not paths:
        print("セッションがありません。")
        return

    total = len(paths)
    approved = 0
    rejected = 0
    pending = 0
    turn_counts = []

    for p in paths:
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
            action = data.get("human_approval", {}).get("action", "pending")
            if action == "approved":
                approved += 1
            elif action == "rejected":
                rejected += 1
            else:
                pending += 1
            turn_counts.append(len(data.get("turns", [])))
        except Exception:
            continue

    avg_turns = round(sum(turn_counts) / len(turn_counts), 1) if turn_counts else 0

    print(f"\n{'='*40}")
    print(f"  セッションサマリー")
    print(f"{'='*40}")
    print(f"  総セッション数 : {total}")
    print(f"  承認           : {approved}")
    print(f"  却下           : {rejected}")
    print(f"  保留           : {pending}")
    print(f"  平均ターン数   : {avg_turns}")
    print(f"{'='*40}\n")


def export_approved_csv(output_path: str = "approved_sessions.csv"):
    """承認済みセッションの一覧をCSV形式で出力"""
    paths = sorted(SESSION_DIR.glob("*.json"))
    rows = []
    for p in paths:
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
            action = data.get("human_approval", {}).get("action", "")
            if action != "approved":
                continue
            turns = data.get("turns", [])
            rows.append({
                "file": p.name,
                "task": data.get("task", ""),
                "result": data.get("result", ""),
                "turns": len(turns),
                "elapsed_sec": sum(t.get("elapsed_sec", 0) for t in turns),
            })
        except Exception:
            continue

    if not rows:
        print("承認済みセッションがありません。")
        return

    out = Path(output_path)
    with open(out, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["file", "task", "result", "turns", "elapsed_sec"])
        writer.writeheader()
        writer.writerows(rows)
    print(f"CSV exported: {out} ({len(rows)} sessions)")


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
    parser.add_argument("--summary", action="store_true", help="承認サマリーを表示")
    parser.add_argument("--export", type=str, nargs="?", const="approved_sessions.csv", default=None, help="承認済みセッションをCSV出力")
    args = parser.parse_args()
    if args.summary:
        show_summary()
    elif args.export is not None:
        export_approved_csv(args.export)
    else:
        run_approval_ui(session_path=args.session)
