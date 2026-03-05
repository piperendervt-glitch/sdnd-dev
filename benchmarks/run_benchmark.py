"""ベンチマーク実行エントリポイント

使い方:
  python -m benchmarks.run_benchmark --task 1
  python -m benchmarks.run_benchmark --all
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from benchmarks.minimal_benchmark import TASKS, get_task, score_before, score_after
from sdnd_dev.agents import Agent

LOG_DIR = Path("sessions/benchmark_logs")


def run_single(task_id: int) -> dict:
    """1タスクを実行してスコアを返す"""
    task = get_task(task_id)
    print(f"\n{'='*50}")
    print(f"タスク {task['id']}: {task['name']}")
    print(f"指示: {task['description']}")
    print(f"{'='*50}")
    print(f"[Before]\n{task['before']}")

    before = score_before(task)
    start = time.time()

    # Implementer にリファクタさせる
    implementer = Agent("implementer")
    messages = [{
        "role": "user",
        "content": (
            f"以下のコードを改善してください。\n"
            f"指示：{task['description']}\n\n"
            f"```python\n{task['before']}\n```\n\n"
            f"改善後のコードのみをコードブロックで出力してください。"
        )
    }]
    response = implementer.respond(messages)
    elapsed = time.time() - start

    # コード抽出
    match = re.search(r"```python\n(.*?)```", response, re.DOTALL)
    after_code = match.group(1).strip() if match else response.strip()

    after = score_after(task, after_code)

    print(f"\n[After]\n{after_code}")
    print(f"\n[スコア] Before: {before:.2f} -> After: {after:.2f} "
          f"(+{after - before:.2f}) / {elapsed:.1f}秒")

    return {
        "task_id": task_id,
        "task_name": task["name"],
        "before_score": before,
        "after_score": after,
        "improvement": round(after - before, 2),
        "elapsed_sec": round(elapsed, 1),
        "after_code": after_code,
    }


def run_all() -> list:
    """全タスクを実行"""
    results = []
    for task in TASKS:
        result = run_single(task["id"])
        results.append(result)

    # サマリー表示
    avg_improvement = sum(r["improvement"] for r in results) / len(results)
    print(f"\n{'='*50}")
    print(f"全タスク完了 / 平均改善: +{avg_improvement:.2f}")
    print(f"{'='*50}")

    return results


def save_log(results: list):
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    path = LOG_DIR / f"{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    path.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nログ保存: {path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--task", type=int, help="タスクID (1-5)")
    parser.add_argument("--all", action="store_true", help="全タスク実行")
    args = parser.parse_args()

    if args.all:
        results = run_all()
        save_log(results)
    elif args.task:
        result = run_single(args.task)
        save_log([result])
    else:
        parser.print_help()
