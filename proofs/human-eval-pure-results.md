# HumanEval-Pure 純粋評価結果（Claude Code介在なし）

## 概要
- モデル: qwen2.5:3b
- タスク数: 8問 (T44〜T51)
- 評価方法: unittest通過率 (pass@1)
- プロンプト: 問題文 + 空の関数テンプレートのみ（良い例/悪い例なし）
- 実行日時: 2026-03-06頃
- 結果: 7/8満点 (pass@1 = 87.5%)

## 詳細結果
| ID | 問題 | テスト通過 | スコア | 備考 |
|----|------|------------|--------|------|
| T44 | 括弧の整合性チェック | 6/6 | 1.00 | - |
| T45 | ローマ数字→整数変換 | 6/6 | 1.00 | - |
| T46 | 最大部分配列和 | 5/5 | 1.00 | - |
| T47 | ソート済みリストのマージ | 5/5 | 1.00 | - |
| T48 | 行列の転置 | 4/4 | 1.00 | - |
| T49 | 文字列圧縮 | 1/5 | 0.36 | エッジケース見落とし |
| T50 | 素数判定 | 6/6 | 1.00 | - |
| T51 | 単語出現頻度 | 5/5 | 1.00 | - |

## 再現方法
```bash
git clone https://github.com/piperendervt-glitch/sdnd-dev.git
cd sdnd-dev
pip install -e ../sdnd-theater  # ollama必要
ollama run qwen2.5:3b

# 個別実行
python -m benchmarks.run_benchmark --task 44
python -m benchmarks.run_benchmark --task 45
# ... (44〜51を個別に実行)

# 全タスク一括実行
python -m benchmarks.run_benchmark --all
```

## 注意
- 3Bモデルの生成揺らぎがあるため、複数回実行で平均を取ることを推奨
- この結果はClaude Codeの介在なしでsdnd-dev単独で出したものです
