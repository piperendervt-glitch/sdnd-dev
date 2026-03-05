"""RSIベンチマーク — 連続サイクル実行 + proofs自動保存

使い方:
  python -m benchmarks.rsi_benchmark --cycles 5
"""

from __future__ import annotations

import argparse
import csv
import io
import json
import re
import sys
import time
from datetime import datetime
from pathlib import Path

# Windows CP932回避
if sys.stdout.encoding != "utf-8":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")

sys.path.insert(0, str(Path(__file__).parent.parent))

from benchmarks.minimal_benchmark import TASKS, score_before, score_after
from sdnd_dev.agents import AGENT_SYSTEMS, TASK_TYPE_HINTS
from core.safety_constitution import get_constitution
from ollama_client import OllamaBackend

LOG_DIR = Path("sessions/rsi_logs")
CSV_PATH = LOG_DIR / "cycles.csv"
PROOFS_DIR = Path("proofs")

# ─────────────────────────────────────────
# ベンチマーク実行
# ─────────────────────────────────────────


def run_one_cycle(system_prompt: str) -> list[dict]:
    """全タスクを1回ずつ実行してスコアを返す"""
    backend = OllamaBackend(model="qwen2.5:3b")
    results = []

    for task in TASKS:
        start = time.time()
        messages = [{
            "role": "user",
            "content": (
                f"以下のコードを改善してください。\n"
                f"指示：{task['description']}\n\n"
                f"```python\n{task['before']}\n```\n\n"
                f"改善後のコードのみをコードブロックで出力してください。"
            ),
        }]

        task_type = task.get("type", "")
        prompt = system_prompt + TASK_TYPE_HINTS.get(task_type, "")
        response = backend.chat(
            system=prompt,
            messages=messages,
            max_output_tokens=1024,
        )
        elapsed = time.time() - start

        match = re.search(r"```python\n(.*?)```", response, re.DOTALL)
        after_code = match.group(1).strip() if match else response.strip()

        before_s = score_before(task)
        after_s = score_after(task, after_code)

        results.append({
            "task_id": task["id"],
            "task_name": task["name"],
            "task_type": task_type,
            "before_score": before_s,
            "after_score": after_s,
            "improvement": round(after_s - before_s, 2),
            "elapsed_sec": round(elapsed, 1),
            "after_code": after_code,
        })

        print(f"    T{task['id']} {task['name']:<14} -> {after_s:.2f} (+{after_s - before_s:.2f}) [{elapsed:.0f}s]")

    return results


# ─────────────────────────────────────────
# テキストグラフ
# ─────────────────────────────────────────


def bar_graph(score: float, width: int = 10) -> str:
    filled = int(round(score * width))
    filled = max(0, min(width, filled))
    return "\u2588" * filled + "\u2591" * (width - filled)


def print_progress(history: list[dict]):
    """全サイクルのテキストグラフを表示"""
    print()
    for entry in history:
        avg = entry["avg"]
        graph = bar_graph(avg)
        print(f"  Cycle {entry['cycle']:>2}: {graph} {avg:.2f}")
    print()


# ─────────────────────────────────────────
# proofs 保存
# ─────────────────────────────────────────


def save_proofs(cycle_num: int, results: list[dict], prompt_used: str):
    """proofs/genN_timestamp/ に各種ログを保存"""
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    proof_dir = PROOFS_DIR / f"gen{cycle_num}_{ts}"
    code_dir = proof_dir / "generated_code"
    code_dir.mkdir(parents=True, exist_ok=True)

    # scores.json
    scores = {
        "cycle": cycle_num,
        "timestamp": datetime.now().isoformat(),
        "tasks": [
            {
                "task_id": r["task_id"],
                "task_name": r["task_name"],
                "before_score": r["before_score"],
                "after_score": r["after_score"],
                "improvement": r["improvement"],
                "elapsed_sec": r["elapsed_sec"],
            }
            for r in results
        ],
        "avg_score": round(sum(r["after_score"] for r in results) / len(results), 2),
    }
    (proof_dir / "scores.json").write_text(
        json.dumps(scores, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    # prompts_used.txt
    (proof_dir / "prompts_used.txt").write_text(prompt_used, encoding="utf-8")

    # constitution_log.txt
    constitution = get_constitution()
    constitution_log = (
        f"=== 安全憲法適用確認 (Cycle {cycle_num}) ===\n\n"
        f"適用: YES\n"
        f"注入先: Implementerシステムプロンプト\n"
        f"バージョン: v0.1\n\n"
        f"--- 憲法テキスト ---\n{constitution}\n"
    )
    (proof_dir / "constitution_log.txt").write_text(constitution_log, encoding="utf-8")

    # summary.md
    lines = [
        f"# Cycle {cycle_num} Summary\n",
        f"| Task | Before | After | Delta |",
        f"|------|--------|-------|-------|",
    ]
    for r in results:
        delta = r["after_score"] - r["before_score"]
        lines.append(f"| {r['task_name']} | {r['before_score']:.2f} | {r['after_score']:.2f} | +{delta:.2f} |")
    avg = scores["avg_score"]
    lines.append(f"\n**Average: {avg:.2f}**\n")
    (proof_dir / "summary.md").write_text("\n".join(lines), encoding="utf-8")

    # generated_code/
    for r in results:
        filename = f"task{r['task_id']}_{r['task_name']}.py"
        # ファイル名に使えない文字を除去
        filename = re.sub(r'[^\w.\-]', '_', filename)
        (code_dir / filename).write_text(r["after_code"], encoding="utf-8")

    return proof_dir


# ─────────────────────────────────────────
# CSV ログ
# ─────────────────────────────────────────


def append_csv(cycle_num: int, results: list[dict]):
    """cycles.csv に1行追記"""
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    scores = [r["after_score"] for r in results]
    avg = round(sum(scores) / len(scores), 2)
    row = [cycle_num] + [round(s, 2) for s in scores] + [avg]

    write_header = not CSV_PATH.exists()
    with open(CSV_PATH, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        if write_header:
            writer.writerow(["cycle", "task1", "task2", "task3", "task4", "task5", "average"])
        writer.writerow(row)


# ─────────────────────────────────────────
# メイン
# ─────────────────────────────────────────


def run_cycles(max_cycles: int = 5):
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    PROOFS_DIR.mkdir(parents=True, exist_ok=True)

    prompt = AGENT_SYSTEMS["implementer"]
    history: list[dict] = []
    stall_count = 0
    total_start = time.time()

    print("=" * 60)
    print(f"RSI 連続サイクル実行 (max {max_cycles} cycles)")
    print("=" * 60)

    for cycle in range(1, max_cycles + 1):
        cycle_start = time.time()
        print(f"\n--- Cycle {cycle}/{max_cycles} ---")

        # ベンチマーク実行
        results = run_one_cycle(prompt)
        avg = round(sum(r["after_score"] for r in results) / len(results), 2)
        elapsed = round(time.time() - cycle_start, 1)

        print(f"  => 平均: {avg:.2f} ({elapsed}s)")

        # 記録
        entry = {
            "cycle": cycle,
            "avg": avg,
            "scores": [r["after_score"] for r in results],
            "elapsed_sec": elapsed,
        }
        history.append(entry)

        # CSV追記
        append_csv(cycle, results)

        # proofs保存
        proof_dir = save_proofs(cycle, results, prompt)
        print(f"  => proofs: {proof_dir}")

        # テキストグラフ
        print_progress(history)

        # 停滞チェック（改善 < 0.01 が2サイクル連続で停止）
        if len(history) >= 2:
            delta = abs(history[-1]["avg"] - history[-2]["avg"])
            if delta < 0.01:
                stall_count += 1
                print(f"  [STALL] 改善 {delta:.3f} < 0.01 ({stall_count}/2)")
                if stall_count >= 2:
                    print(f"\n  [AUTO-STOP] 2サイクル連続で停滞 -> 自動停止")
                    break
            else:
                stall_count = 0

    # 最終サマリー
    total_elapsed = round(time.time() - total_start, 1)
    print("\n" + "=" * 60)
    print("最終結果")
    print("=" * 60)

    print(f"\n{'Cycle':>6} {'T1':>6} {'T2':>6} {'T3':>6} {'T4':>6} {'T5':>6} {'Avg':>8}")
    print("-" * 50)
    for h in history:
        scores_str = " ".join(f"{s:>6.2f}" for s in h["scores"])
        print(f"{h['cycle']:>6} {scores_str} {h['avg']:>8.2f}")
    print("-" * 50)

    # 推移グラフ
    print("\nスコア推移:")
    print_progress(history)

    # 分析
    if len(history) >= 2:
        first_avg = history[0]["avg"]
        last_avg = history[-1]["avg"]
        total_delta = last_avg - first_avg
        marker = "+" if total_delta >= 0 else ""
        print(f"総合改善: {marker}{total_delta:.2f} (Cycle 1: {first_avg:.2f} -> Cycle {history[-1]['cycle']}: {last_avg:.2f})")

        # 頭打ち/低下の検出
        for i in range(1, len(history)):
            delta = history[i]["avg"] - history[i - 1]["avg"]
            if delta < -0.02:
                print(f"  [WARN] Cycle {history[i]['cycle']}: スコア低下 {delta:.2f}")
                # 低下したタスクを特定
                for j, (prev, curr) in enumerate(zip(history[i - 1]["scores"], history[i]["scores"])):
                    if curr < prev - 0.05:
                        print(f"    -> タスク{j + 1}: {prev:.2f} -> {curr:.2f}")

    print(f"\n合計所要時間: {total_elapsed}s")
    print(f"CSV: {CSV_PATH}")
    print(f"Proofs: {PROOFS_DIR}/")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="RSI連続サイクル実行")
    parser.add_argument("--cycles", type=int, default=5, help="サイクル数 (default: 5)")
    args = parser.parse_args()
    run_cycles(max_cycles=args.cycles)
