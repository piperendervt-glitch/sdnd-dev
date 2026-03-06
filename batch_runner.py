"""バッチ実行ツール

task_pool.json からタスクを選択し、dev_scenario.py のセッションを
連続実行する。ログは sessions/batch/ に保存。

使い方:
  python batch_runner.py --count 10
  python batch_runner.py --count 1000 --quiet --no-review
  python batch_runner.py --count 5 --sequential
"""

from __future__ import annotations

import argparse
import json
import random
import sys
import time
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from sdnd_dev.dev_scenario import run_session

TASK_POOL_PATH = Path(__file__).parent / "task_pool.json"
BATCH_LOG_DIR = Path(__file__).parent / "sessions" / "batch"


def load_task_pool() -> list[dict]:
    return json.loads(TASK_POOL_PATH.read_text(encoding="utf-8"))


def run_batch(
    count: int = 10,
    sequential: bool = False,
    quiet: bool = False,
    human_review: bool = True,
) -> list[dict]:
    pool = load_task_pool()
    BATCH_LOG_DIR.mkdir(parents=True, exist_ok=True)

    if sequential:
        # 順番に選択（countがプール数を超えたら繰り返す）
        tasks = [pool[i % len(pool)] for i in range(count)]
    else:
        tasks = [random.choice(pool) for _ in range(count)]

    results = []
    start_time = time.time()

    for i, task_entry in enumerate(tasks, 1):
        task_id = task_entry["task_id"]
        task_name = task_entry["name"]
        task_desc = f"[{task_id}] {task_name}"

        print(f"\n[{i}/{count}] {task_desc}")

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = str(BATCH_LOG_DIR / f"{timestamp}_{task_id}.json")

        log = run_session(
            task=task_name,
            human_review=human_review,
            quiet=quiet,
            output=output_path,
        )

        result = log["result"]
        results.append({"task_id": task_id, "name": task_name, "result": result})
        print(f"  -> {result}")

    elapsed = round(time.time() - start_time, 1)
    approved = sum(1 for r in results if r["result"] == "approved")

    print(f"\n{'=' * 60}")
    print(f"  Batch Results: {count} runs ({elapsed}s)")
    print(f"  Approved : {approved}/{count} ({round(approved / count * 100, 1)}%)")
    print(f"  Log dir  : {BATCH_LOG_DIR}")
    print(f"{'=' * 60}")

    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="SDND Batch Runner - task_pool.json からバッチ実行")
    parser.add_argument("--count", type=int, default=10, help="実行件数（デフォルト10）")
    parser.add_argument("--random", action="store_true", default=True, help="ランダム選択（デフォルト）")
    parser.add_argument("--sequential", action="store_true", help="順番に選択")
    parser.add_argument("--quiet", action="store_true", help="ログ簡略化")
    parser.add_argument("--no-review", action="store_true", help="human_review なしで実行")
    args = parser.parse_args()

    run_batch(
        count=args.count,
        sequential=args.sequential,
        quiet=args.quiet,
        human_review=not args.no_review,
    )
