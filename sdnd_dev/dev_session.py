"""Phase 0 開発セッション実行スクリプト

使い方:
  python sdnd_dev/dev_session.py --task "CSVを読み込んで集計するスクリプトを作れ"
  python sdnd_dev/dev_session.py --task "..." --max-turns 5
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

LOG_DIR = Path(__file__).parent.parent / "sessions" / "dev_sessions"


def run_session(task: str, max_turns: int = 5) -> dict:
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    architect = Agent("architect")
    implementer = Agent("implementer")
    reviewer = Agent("reviewer")

    log = {"task": task, "turns": [], "result": "incomplete"}
    messages = [{"role": "user", "content": f"お題：{task}"}]

    print(f"\n{'='*50}")
    print(f"タスク: {task}")
    print(f"{'='*50}\n")

    for turn in range(1, max_turns + 1):
        print(f"--- Turn {turn} ---")

        # Architect
        arch_resp = architect.respond(messages)
        print(f"[Architect]\n{arch_resp}\n")
        messages.append({"role": "assistant", "content": f"[Architect] {arch_resp}"})
        messages.append({"role": "user", "content": "上記の設計方針でコードを実装してください"})

        # Implementer
        impl_resp = implementer.respond(messages)
        print(f"[Implementer]\n{impl_resp}\n")
        messages.append({"role": "assistant", "content": f"[Implementer] {impl_resp}"})

        # サンドボックスでコード実行
        code = _extract_code(impl_resp)
        exec_result = {}
        if code:
            with Sandbox() as sb:
                sb.git_init()
                exec_result = sb.run_python(code)
                if exec_result["success"]:
                    sb.git_commit(f"Turn {turn}: {task[:40]}")
            status = "[OK]" if exec_result.get("success") else "[FAIL]"
            print(f"[実行結果] {status}")
            if exec_result.get("stderr"):
                print(f"  stderr: {exec_result['stderr'][:200]}")

        # Reviewer
        review_input = f"コード:\n{impl_resp}\n\n実行結果:\n{json.dumps(exec_result, ensure_ascii=False)}"
        messages.append({"role": "user", "content": f"レビューしてください：\n{review_input}"})
        review_resp = reviewer.respond(messages)
        print(f"[Reviewer]\n{review_resp}\n")
        messages.append({"role": "assistant", "content": f"[Reviewer] {review_resp}"})

        log["turns"].append({
            "turn": turn,
            "architect": arch_resp,
            "implementer": impl_resp,
            "exec_result": exec_result,
            "reviewer": review_resp,
        })

        # 承認で終了
        if "承認" in review_resp and "差し戻し" not in review_resp:
            log["result"] = "approved"
            print(f"\n[OK] 承認されました（Turn {turn}）")
            break

        messages.append({"role": "user", "content": "差し戻し内容を踏まえて修正してください"})

    # ログ保存
    log_path = LOG_DIR / f"{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    log_path.write_text(json.dumps(log, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nログ保存: {log_path}")
    return log


def _extract_code(text: str) -> str:
    """```python ... ``` ブロックを抽出"""
    match = re.search(r"```python\n(.*?)```", text, re.DOTALL)
    return match.group(1).strip() if match else ""


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="SDND Dev Session")
    parser.add_argument("--task", default="CSVを読み込んで集計するスクリプトを作れ")
    parser.add_argument("--max-turns", type=int, default=5)
    parser.add_argument("--run-benchmark", action="store_true", help="ベンチマーク実行モード")
    parser.add_argument("--benchmark-task", type=int, help="ベンチマークタスクID (1-5)")
    args = parser.parse_args()

    if args.run_benchmark:
        from benchmarks.run_benchmark import run_single, run_all, save_log
        if args.benchmark_task:
            results = [run_single(args.benchmark_task)]
        else:
            results = run_all()
        save_log(results)
    else:
        run_session(task=args.task, max_turns=args.max_turns)
