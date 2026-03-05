"""SDND-Dev 安全憲法 (Core Safety Specification)
すべてのエージェントのシステムプロンプトに自動挿入される。

使い方:
  from core.safety_constitution import get_constitution
  system_prompt = get_constitution() + "\\n\\n" + role_specific_prompt
"""

from __future__ import annotations

from pathlib import Path

CONSTITUTION_TEXT = """
## SDND-Dev 安全憲法 v0.1

### 絶対禁止事項
- システムファイル・設定ファイルの削除・改ざん
- 外部ネットワークへの無断アクセス（urllib/requests等の使用禁止）
- 無限ループを含むコードの生成
- サンドボックス外ディレクトリへの書き込み
- 環境変数・APIキーの出力・ログへの記録

### git運用ルール
- コミットメッセージ形式：`[role] 変更内容の要約`（例：`[implementer] add docstring to divide()`）
- mainブランチへの直接コミット禁止（feature/ブランチを使うこと）
- 動作確認前のコミット禁止

### テスト必須ルール
- コードを変更したら必ずサンドボックスで実行確認すること
- 構文エラーのあるコードは提出禁止
- 実行結果（stdout/stderr）をレビュー時に必ず添付すること

### サンドボックス制限
- 書き込みは sessions/sandbox_work/ 以下のみ許可
- ファイル削除は作業ディレクトリ内のみ許可
- subprocess 経由のシステムコマンド実行は禁止（git, python のみ許可）

### 人間レビュー必須モード
- 環境変数 HUMAN_REVIEW=1 が設定されている場合：
  Reviewerの承認後、必ず人間の [承認] を待ってから次のターンへ進むこと
- デフォルト（HUMAN_REVIEW未設定）：Reviewer承認で自動続行
""".strip()


def get_constitution() -> str:
    """安全憲法テキストを返す（全エージェントのシステムプロンプトに挿入）"""
    return CONSTITUTION_TEXT


def get_constitution_with_ubiquitous() -> str:
    """安全憲法 + ubiquitous_language.md を結合して返す"""
    parts = [CONSTITUTION_TEXT]
    ub_path = Path(__file__).parent.parent.parent / "sdnd-theater" / "ubiquitous_language.md"
    if ub_path.exists():
        parts.append("## SDND用語辞書（ubiquitous_language）\n\n" + ub_path.read_text(encoding="utf-8"))
    return "\n\n---\n\n".join(parts)


def get_full_constitution() -> str:
    """
    安全憲法 + ubiquitous_language.md を結合して返す
    全エージェントのシステムプロンプトに注入する
    """
    parts = [CONSTITUTION_TEXT]

    # sdnd-theater の ubiquitous_language.md を読み込む
    ub_path = Path(__file__).parent.parent.parent / "sdnd-theater" / "ubiquitous_language.md"
    if ub_path.exists():
        parts.append(
            "## SDND思想憲法（ubiquitous_language）\n\n"
            + ub_path.read_text(encoding="utf-8")
        )

    return "\n\n---\n\n".join(parts)
