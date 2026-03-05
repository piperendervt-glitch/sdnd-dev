# sdnd-dev

## 概要

複数AIエージェントが協調してソフトウェアを自律改善する実験的フレームワーク。
sdnd-theater（TRPGセッション生成）の姉妹プロジェクト。

3つのエージェント（Architect / Implementer / Reviewer）が対話しながら、
コード生成・実行・レビューのサイクルを自律的に回す。

## 依存関係

- [sdnd-theater](https://github.com/piperendervt-glitch/sdnd-theater) — LLMバックエンド (`ollama_client.py`) を提供
- [Ollama](https://ollama.com/) — ローカルLLM実行環境（モデル: `qwen2.5:3b`）

## クイックスタート

```bash
# 1. sdnd-theater をインストール
pip install -e ../sdnd-theater

# 2. Ollama を起動
ollama serve

# 3. 開発セッション実行
python sdnd_dev/dev_session.py --task "CSVを読み込んで集計するスクリプトを作れ"

# 4. ベンチマーク実行（全5タスク）
python -m benchmarks.run_benchmark --all

# 5. RSI（自己改善サイクル）実行
python -m benchmarks.rsi_benchmark
```

## ディレクトリ構成

```
sdnd-dev/
├── sdnd_dev/                  # メインモジュール
│   ├── __init__.py
│   ├── agents.py              # 多エージェント構成（Architect/Implementer/Reviewer）
│   ├── constitution.md        # 安全憲法（Markdownソース）
│   ├── dev_session.py         # 開発セッション エントリポイント
│   └── sandbox.py             # コード実行サンドボックス
├── core/                      # コア機能
│   ├── __init__.py
│   └── safety_constitution.py # 安全憲法（プログラム的に注入）
├── benchmarks/                # ベンチマーク
│   ├── __init__.py
│   ├── minimal_benchmark.py   # タスク定義 + スコアリング
│   ├── run_benchmark.py       # ベンチマーク実行
│   └── rsi_benchmark.py       # RSI自己改善サイクル
├── sessions/                  # セッションログ（gitignore対象）
│   ├── dev_sessions/          # 開発セッションログ
│   ├── benchmark_logs/        # ベンチマーク結果
│   ├── rsi_logs/              # RSIサイクルログ
│   └── sandbox_work/          # サンドボックス一時ディレクトリ
├── .gitignore
├── .env.example
└── README.md
```

## ライセンス

MIT
