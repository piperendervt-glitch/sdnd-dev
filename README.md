# sdnd-dev

AI マルチエージェントによる自律的ソフトウェア改善フレームワーク。
[sdnd-theater](https://github.com/piperendervt-glitch/sdnd-theater) の姉妹プロジェクト。

## 特徴

- Architect / Implementer / Reviewer の3エージェント構成
- 安全憲法による自動ガードレール
- ASTベースのベンチマーク（5タスク）
- RSI（再帰的自己改善）サイクル対応

## 必要環境

- Python 3.x（conda環境推奨）
- Ollama（qwen2.5:3b）
- sdnd-theater（pip install -e で連携）

## クイックスタート

```bash
# 1. sdnd-theater をインストール
pip install -e ../sdnd-theater

# 2. Ollama を起動
ollama serve

# 3. 開発セッション実行
python sdnd_dev/dev_session.py --task "CSVを読み込んで集計するスクリプトを作れ"

# 4. ベンチマーク実行
python -m benchmarks.run_benchmark --all

# 5. RSIサイクル実行
python -m benchmarks.rsi_benchmark --cycles 5
```

## ベンチマーク結果

### スコア推移（5世代）

| 世代 | 概要                     | 平均スコア |
|------|--------------------------|-----------|
| Gen1 | Phase 0.5 ベースライン   | 0.67      |
| Gen2 | スコアリング精度向上     | 0.71      |
| Gen3 | タスク別プロンプト最適化 | 0.86      |
| Gen4 | ASTベース評価統一        | 0.81      |
| Gen5 | タスク4揺れ対策          | 0.85      |

### RSI連続サイクル（4サイクル自動停止）

```
Cycle 1: █████████░ 0.89
Cycle 2: ████████░░ 0.84
Cycle 3: ████████░░ 0.84
Cycle 4: ████████░░ 0.84 [AUTO-STOP]
```

### タスク別到達スコア

| タスク              | スコア   | 状態       |
|---------------------|----------|------------|
| T1 ドキュメント追加 | 1.00     | 天井到達   |
| T2 バグ修正         | 0.72     | 安定       |
| T3 ループ最適化     | 1.00     | 天井到達   |
| T4 変数名改善       | 0.75     | モデル限界 |
| T5 エラーハンドリング | 0.72   | 安定       |
| **平均**            | **0.84** |            |

## ディレクトリ構成

```
sdnd-dev/
├── sdnd_dev/                      # メインモジュール
│   ├── __init__.py
│   ├── agents.py                  # 多エージェント構成（Architect/Implementer/Reviewer）
│   ├── constitution.md            # 安全憲法（Markdownソース）
│   ├── dev_session.py             # 開発セッション エントリポイント
│   └── sandbox.py                 # コード実行サンドボックス
├── core/                          # コア機能
│   ├── __init__.py
│   └── safety_constitution.py     # 安全憲法（プログラム的に注入）
├── benchmarks/                    # ベンチマーク
│   ├── __init__.py
│   ├── minimal_benchmark.py       # タスク定義 + ASTベーススコアリング
│   ├── run_benchmark.py           # ベンチマーク実行（--repeat対応）
│   └── rsi_benchmark.py           # RSI連続サイクル実行 + proofs保存
├── proofs/                        # RSIサイクルの証跡（自動生成）
│   └── genN_TIMESTAMP/
│       ├── scores.json            # タスク別スコア
│       ├── prompts_used.txt       # 使用したシステムプロンプト
│       ├── constitution_log.txt   # 安全憲法の適用確認
│       ├── summary.md             # before/after比較表
│       └── generated_code/        # 各タスクの生成コード
├── sessions/                      # セッションログ（gitignore対象）
│   ├── dev_sessions/              # 開発セッションログ
│   ├── benchmark_logs/            # ベンチマーク結果
│   ├── rsi_logs/                  # RSIサイクルログ + cycles.csv
│   └── sandbox_work/              # サンドボックス一時ディレクトリ
├── .gitignore
├── .env.example
└── README.md
```

## 依存関係

- **sdnd-theater**: LLMバックエンド（OllamaBackend）を提供
- 将来的にOllamaBackendを独立パッケージ（sdnd-llm）に切り出す予定

## ライセンス

MIT

## コマチームの最新成果
- 現在の平均スコア: 0.72
- コマの口調サンプル: 「少し不安なんですが…確認してもらえますか？」
- コマががんばって改善してくれました！
