"""RSIベンチマーク — プロンプト自己改善サイクル

手順:
  1. 全タスクベンチマーク実行 (baseline)
  2. Architect がスコア分析・改善案を提示
  3. Implementer が改善プロンプトを生成
  4. 改善プロンプトで再ベンチマーク実行
  5. before/after 比較

使い方:
  python -m benchmarks.rsi_benchmark
"""

from __future__ import annotations

import json
import re
import sys
import time
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from benchmarks.minimal_benchmark import TASKS, get_task, score_before, score_after
from sdnd_dev.agents import Agent, AGENT_SYSTEMS
from ollama_client import OllamaBackend

LOG_DIR = Path("sessions/rsi_logs")


def run_benchmark_with_prompt(system_prompt: str) -> list[dict]:
    """指定システムプロンプトでImplementerを動かしベンチマーク実行"""
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

        response = backend.chat(
            system=system_prompt,
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
            "before_score": before_s,
            "after_score": after_s,
            "improvement": round(after_s - before_s, 2),
            "elapsed_sec": round(elapsed, 1),
            "after_code": after_code,
        })

        print(f"  タスク {task['id']}: {task['name']} -> {after_s:.2f} (+{after_s - before_s:.2f}) [{elapsed:.1f}s]")

    return results


def analyze_and_improve(baseline_results: list) -> str:
    """Architect分析 → Implementerが改善プロンプトを生成"""
    # スコアレポート作成
    report_lines = []
    for r in baseline_results:
        report_lines.append(
            f"タスク{r['task_id']} ({r['task_name']}): "
            f"スコア {r['after_score']:.2f} / 改善 +{r['improvement']:.2f}"
        )
        if r["after_score"] < 0.6:
            report_lines.append(f"  [低スコア] 生成コード: {r['after_code'][:100]}...")
    report = "\n".join(report_lines)

    avg = sum(r["after_score"] for r in baseline_results) / len(baseline_results)
    report += f"\n\n平均スコア: {avg:.2f}"

    # Architect: 分析
    print("\n[Architect] スコア分析中...")
    architect = Agent("architect")
    arch_messages = [{
        "role": "user",
        "content": (
            f"以下はコード改善ベンチマークの結果です。\n\n{report}\n\n"
            f"スコアが低いタスクの原因を分析し、"
            f"Implementerのシステムプロンプトをどう改善すべきか、"
            f"具体的に3つの改善案を提示してください。"
        ),
    }]
    arch_resp = architect.respond(arch_messages)
    print(f"{arch_resp}\n")

    # Implementer: 改善プロンプト生成
    print("[Implementer] 改善プロンプト生成中...")
    current_prompt = AGENT_SYSTEMS["implementer"]
    gen_backend = OllamaBackend(model="qwen2.5:3b")
    gen_messages = [{
        "role": "user",
        "content": (
            f"あなたはプロンプトエンジニアです。\n\n"
            f"現在のImplementerシステムプロンプト:\n```\n{current_prompt[:500]}\n```\n\n"
            f"Architectの改善提案:\n{arch_resp}\n\n"
            f"上記を踏まえ、改善されたImplementerシステムプロンプトを生成してください。\n"
            f"出力はプロンプト本文のみ（```で囲まないこと）。\n"
            f"日本語で、300文字以内で簡潔に。"
        ),
    }]
    improved_prompt = gen_backend.chat(
        system="あなたはプロンプト最適化の専門家です。改善されたシステムプロンプトのみを出力してください。",
        messages=gen_messages,
        max_output_tokens=512,
    )
    print(f"[改善プロンプト]\n{improved_prompt}\n")

    return improved_prompt.strip()


def run_rsi_cycle():
    """RSI 1サイクル実行"""
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    cycle_start = time.time()

    print("=" * 60)
    print("RSI ベンチマーク自己改善サイクル")
    print("=" * 60)

    # Phase 1: Baseline
    print("\n[Phase 1] Baseline ベンチマーク実行")
    print("-" * 40)
    original_prompt = AGENT_SYSTEMS["implementer"]
    baseline = run_benchmark_with_prompt(original_prompt)
    baseline_avg = sum(r["after_score"] for r in baseline) / len(baseline)
    print(f"\nBaseline 平均スコア: {baseline_avg:.2f}")

    # Phase 2-3: 分析 + 改善プロンプト生成
    print("\n[Phase 2-3] 分析・改善プロンプト生成")
    print("-" * 40)
    improved_prompt = analyze_and_improve(baseline)

    # Phase 4: 改善後ベンチマーク
    print("\n[Phase 4] 改善プロンプトでベンチマーク再実行")
    print("-" * 40)
    improved = run_benchmark_with_prompt(improved_prompt)
    improved_avg = sum(r["after_score"] for r in improved) / len(improved)
    print(f"\n改善後 平均スコア: {improved_avg:.2f}")

    # Phase 5: 比較
    cycle_elapsed = time.time() - cycle_start
    print("\n" + "=" * 60)
    print("[Phase 5] Before / After 比較")
    print("=" * 60)
    print(f"{'タスク':<20} {'Baseline':>10} {'Improved':>10} {'差分':>10}")
    print("-" * 50)
    for b, i in zip(baseline, improved):
        diff = i["after_score"] - b["after_score"]
        marker = "+" if diff > 0 else ""
        print(f"{b['task_name']:<20} {b['after_score']:>10.2f} {i['after_score']:>10.2f} {marker}{diff:>9.2f}")
    print("-" * 50)
    diff_avg = improved_avg - baseline_avg
    marker = "+" if diff_avg > 0 else ""
    print(f"{'平均':<20} {baseline_avg:>10.2f} {improved_avg:>10.2f} {marker}{diff_avg:>9.2f}")
    print(f"\n合計所要時間: {cycle_elapsed:.0f}秒")

    # ログ保存
    log = {
        "timestamp": datetime.now().isoformat(),
        "cycle_elapsed_sec": round(cycle_elapsed, 1),
        "original_prompt": original_prompt[:200] + "...",
        "improved_prompt": improved_prompt,
        "baseline": {"avg_score": round(baseline_avg, 2), "results": baseline},
        "improved": {"avg_score": round(improved_avg, 2), "results": improved},
        "delta_avg": round(diff_avg, 2),
    }
    log_path = LOG_DIR / f"rsi_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    log_path.write_text(json.dumps(log, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nログ保存: {log_path}")


if __name__ == "__main__":
    run_rsi_cycle()
