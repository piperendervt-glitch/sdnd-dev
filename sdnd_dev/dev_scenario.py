"""シナリオ5: 複数AIソフトウェア開発シナリオ

Architect / Implementer / Reviewer の3エージェントが協調して
ソフトウェア開発タスクに取り組む。

終了条件: Reviewer 承認 or 最大ターン数(デフォルト5)で強制終了
ログ保存先: sessions/dev_scenario/

使い方:
  python sdnd_dev/dev_scenario.py
  python sdnd_dev/dev_scenario.py --task "FizzBuzzを実装せよ"
  python sdnd_dev/dev_scenario.py --max-turns 3
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime
from pathlib import Path

# sdnd-dev ルートをパスに追加（直接実行時用）
sys.path.insert(0, str(Path(__file__).parent.parent))

from sdnd_dev.agents import Agent
from sdnd_dev.sandbox import Sandbox
from sdnd_dev.approval_ui import show_session, prompt_approval
from core.safety_constitution import get_full_constitution

# ── 定数 ─────────────────────────────────────────────

DEFAULT_TASK = "CSVを読み込んで集計するスクリプトを作れ"
MAX_TURNS = 5
LOG_DIR = Path(__file__).parent.parent / "sessions" / "dev_scenario"

# ── 思想憲法 ─────────────────────────────────────────
PHILOSOPHY = get_full_constitution()

REVIEWER_PHILOSOPHY_CHECK = """
コードが動作するなら「承認」、問題があれば「差し戻し：（理由）」と書くこと。
"""

# ── ヘルパー ──────────────────────────────────────────


def _extract_code(text: str) -> str:
    """```python ... ``` ブロックからコードを抽出する。"""
    match = re.search(r"```python\n(.*?)```", text, re.DOTALL)
    return match.group(1).strip() if match else ""


# ── メインセッション ─────────────────────────────────


DUMMY_RESPONSES = {
    "architect": "[dry-run] 設計方針：お題に対しシンプルな関数を1つ作成します。",
    "implementer": '[dry-run] ```python\ndef hello():\n    print("hello")\n\nhello()\n```',
    "reviewer": "[dry-run] コードは正常に動作しています。承認",
}


def run_session(
    task: str = DEFAULT_TASK,
    max_turns: int = MAX_TURNS,
    human_review: bool = False,
    dry_run: bool = False,
) -> dict:
    """開発セッションを実行する。"""
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    architect = Agent("architect")
    implementer = Agent("implementer")
    reviewer = Agent("reviewer")

    # Reviewer に思想チェック項目を追加注入（PHILOSOPHY は agents.py で注入済み）
    reviewer.system = reviewer.system + "\n" + REVIEWER_PHILOSOPHY_CHECK

    log = {"task": task, "turns": [], "result": "incomplete"}
    messages: list[dict] = [{"role": "user", "content": f"お題：{task}"}]

    print(f"\n{'=' * 60}")
    print(f"  SDND Dev Scenario")
    print(f"  task: {task}")
    print(f"  max_turns: {max_turns}")
    print(f"{'=' * 60}\n")

    for turn in range(1, max_turns + 1):
        print(f"--- Turn {turn}/{max_turns} ---\n")

        # ── Architect ──
        arch_resp = DUMMY_RESPONSES["architect"] if dry_run else architect.respond(messages)
        print(f"[Architect]\n{arch_resp}\n")
        messages.append({"role": "assistant", "content": f"[Architect] {arch_resp}"})
        messages.append({"role": "user", "content": "上記の設計方針でコードを実装してください。"})

        # ── Implementer ──
        impl_resp = DUMMY_RESPONSES["implementer"] if dry_run else implementer.respond(messages)
        print(f"[Implementer]\n{impl_resp}\n")
        messages.append({"role": "assistant", "content": f"[Implementer] {impl_resp}"})

        # ── コード実行（サンドボックス） ──
        code = _extract_code(impl_resp)
        exec_result: dict = {}
        if code:
            with Sandbox() as sb:
                sb.git_init()
                exec_result = sb.run_python(code)
                if exec_result["success"]:
                    sb.git_commit(f"Turn {turn}: {task[:40]}")
            status = "OK" if exec_result["success"] else "FAIL"
            print(f"[Exec] {status}")
            if exec_result.get("stdout"):
                print(f"  stdout: {exec_result['stdout'][:300]}")
            if exec_result.get("stderr"):
                print(f"  stderr: {exec_result['stderr'][:300]}")
            print()

        # ── Reviewer ──
        review_input = (
            f"コード:\n{impl_resp}\n\n"
            f"実行結果:\n{json.dumps(exec_result, ensure_ascii=False)}"
        )
        messages.append({"role": "user", "content": f"レビューしてください：\n{review_input}"})
        review_resp = DUMMY_RESPONSES["reviewer"] if dry_run else reviewer.respond(messages)
        print(f"[Reviewer]\n{review_resp}\n")
        messages.append({"role": "assistant", "content": f"[Reviewer] {review_resp}"})

        # ── ターンログ ──
        log["turns"].append({
            "turn": turn,
            "architect": arch_resp,
            "implementer": impl_resp,
            "code": code,
            "exec_result": exec_result,
            "reviewer": review_resp,
        })

        # ── 終了判定: Reviewer 承認 ──
        if "承認" in review_resp and "差し戻し" not in review_resp:
            log["result"] = "approved"
            print(f"[APPROVED] Turn {turn} で承認されました。\n")

            # ── human-review モード：人間の最終承認 ──
            if human_review:
                print("[HUMAN REVIEW] 人間の最終承認を待っています...\n")
                show_session(log)
                action, comment = prompt_approval()

                if action == "approved":
                    log["human_approval"] = {"action": "approved", "comment": ""}
                    print("[HUMAN APPROVED] 人間が承認しました。\n")
                elif action == "rejected":
                    log["result"] = "rejected"
                    log["human_approval"] = {"action": "rejected", "comment": ""}
                    print("[HUMAN REJECTED] 人間が却下しました。\n")
                elif action == "sendback":
                    log["human_approval"] = {"action": "sendback", "comment": comment}
                    print(f"[HUMAN SENDBACK] 差し戻し: {comment}\n")
                    messages.append({"role": "user", "content": f"人間からの差し戻し：{comment}\n修正してください。"})
                    continue

            break

        # 差し戻し → 次ターンへ
        messages.append({"role": "user", "content": "差し戻し内容を踏まえて修正してください。"})

    else:
        log["result"] = "max_turns_reached"
        print(f"[TIMEOUT] {max_turns} ターンで終了（強制打ち切り）\n")

    # ── human_approval 初期化（未設定の場合） ──
    if "human_approval" not in log:
        log["human_approval"] = {"action": "pending", "comment": ""}

    # ── ログ保存 ──
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_path = LOG_DIR / f"{timestamp}.json"
    log_path.write_text(json.dumps(log, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Log saved: {log_path}")
    return log


# ── CLI ───────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="SDND Dev Scenario - Multi-Agent Development")
    parser.add_argument("--task", default=DEFAULT_TASK, help="開発タスク")
    parser.add_argument("--max-turns", type=int, default=MAX_TURNS, help="最大ターン数")
    parser.add_argument("--human-review", action="store_true", help="Reviewer承認後に人間の最終承認を待つ")
    parser.add_argument("--dry-run", action="store_true", help="LLMを呼ばずダミーテキストでフロー確認")
    args = parser.parse_args()
    run_session(task=args.task, max_turns=args.max_turns, human_review=args.human_review, dry_run=args.dry_run)
