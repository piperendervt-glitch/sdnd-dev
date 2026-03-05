"""ベンチマーク実行エントリポイント

使い方:
  python -m benchmarks.run_benchmark --task 1
  python -m benchmarks.run_benchmark --all
"""

from __future__ import annotations

import argparse
import io
import json
import re
import sys
import time
from datetime import datetime
from pathlib import Path

# Windows CP932エンコードエラー回避
if sys.stdout.encoding != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

sys.path.insert(0, str(Path(__file__).parent.parent))

from benchmarks.minimal_benchmark import TASKS, get_task, score_before, score_after
from sdnd_dev.agents import Agent, DEFAULT_MODEL

LOG_DIR = Path("sessions/benchmark_logs")


def run_single(task_id: int, model: str = DEFAULT_MODEL) -> dict:
    """1タスクを実行してスコアを返す"""
    task = get_task(task_id)
    print(f"\n{'='*50}")
    print(f"タスク {task['id']}: {task['name']}")
    print(f"指示: {task['description']}")
    print(f"{'='*50}")
    print(f"[Before]\n{task['before']}")

    before = score_before(task)
    start = time.time()

    # Implementer にリファクタ/実装させる
    implementer = Agent("implementer", model=model)
    if task.get("type") == "humaneval":
        prompt = (
            f"以下の関数を正しく実装してください。\n"
            f"問題：{task['description']}\n\n"
            f"関数テンプレート：\n"
            f"```python\n{task['before']}\n```\n\n"
            f"注意：\n"
            f"- 関数名・引数名は変更しないこと\n"
            f"- 関数の実装のみをコードブロックで出力すること\n"
            f"- import文が必要なら関数の外に書くこと\n"
            f"- 説明は不要、コードのみ出力すること\n\n"
            f"実装後のコードのみをコードブロックで出力してください。"
        )
    else:
        prompt = (
            f"以下のコードを改善してください。\n"
            f"指示：{task['description']}\n\n"
            f"```python\n{task['before']}\n```\n\n"
            f"改善後のコードのみをコードブロックで出力してください。"
        )
    messages = [{"role": "user", "content": prompt}]
    response = implementer.respond(messages, task_type=task.get("type"))
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


def run_all(model: str = DEFAULT_MODEL) -> list:
    """全タスクを実行"""
    results = []
    for task in TASKS:
        result = run_single(task["id"], model=model)
        results.append(result)

    # サマリー表示
    avg_improvement = sum(r["improvement"] for r in results) / len(results)
    print(f"\n{'='*50}")
    print(f"全タスク完了 / 平均改善: +{avg_improvement:.2f}")
    print(f"{'='*50}")

    return results


def run_repeated(task_id: int, repeat: int, model: str = DEFAULT_MODEL) -> list[dict]:
    """同一タスクを複数回実行して統計を表示"""
    scores = []
    all_results = []
    for i in range(1, repeat + 1):
        print(f"\n--- Run {i}/{repeat} ---")
        result = run_single(task_id, model=model)
        scores.append(result["after_score"])
        all_results.append(result)

    avg = sum(scores) / len(scores)
    mn, mx = min(scores), max(scores)
    print(f"\n{'='*50}")
    print(f"タスク {task_id} x {repeat}回")
    print(f"  平均: {avg:.2f} / 最小: {mn:.2f} / 最大: {mx:.2f}")
    print(f"  全スコア: {[round(s, 2) for s in scores]}")
    print(f"{'='*50}")

    return all_results


def save_log(results: list):
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    path = LOG_DIR / f"{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    path.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nログ保存: {path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--task", type=int, help="タスクID (1-51)")
    parser.add_argument("--all", action="store_true", help="全タスク実行")
    parser.add_argument("--repeat", type=int, default=1, help="同一タスクの繰り返し回数")
    parser.add_argument("--model", type=str, default=DEFAULT_MODEL, help=f"Ollamaモデル名 (default: {DEFAULT_MODEL})")
    args = parser.parse_args()

    if args.all:
        if args.repeat > 1:
            all_cycle_results = []
            for cycle in range(1, args.repeat + 1):
                print(f"\n{'#'*50}")
                print(f"  Cycle {cycle}/{args.repeat}")
                print(f"{'#'*50}")
                results = run_all(model=args.model)
                avg = sum(r["improvement"] for r in results) / len(results)
                all_cycle_results.append({"cycle": cycle, "avg_improvement": round(avg, 2), "results": results})
                save_log(results)
            # サマリー表示
            print(f"\n{'='*50}")
            print(f"  全サイクル完了 ({args.repeat} cycles)")
            print(f"{'='*50}")
            for cr in all_cycle_results:
                print(f"  Cycle {cr['cycle']}: avg +{cr['avg_improvement']:.2f}")
            overall = sum(cr["avg_improvement"] for cr in all_cycle_results) / len(all_cycle_results)
            print(f"  Overall avg: +{overall:.2f}")
            print(f"{'='*50}")
        else:
            results = run_all(model=args.model)
            save_log(results)
    elif args.task:
        if args.repeat > 1:
            results = run_repeated(args.task, args.repeat, model=args.model)
        else:
            results = [run_single(args.task, model=args.model)]
        save_log(results)
    else:
        parser.print_help()
