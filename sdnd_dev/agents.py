"""Phase 0 最小多エージェント実装"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from ollama_client import OllamaBackend
from core.safety_constitution import get_constitution_with_ubiquitous


def _load_philosophy() -> str:
    """安全憲法 + ubiquitous_language を読み込む"""
    return get_constitution_with_ubiquitous()


PHILOSOPHY = _load_philosophy()

AGENT_SYSTEMS = {
    "architect": f"""あなたはSDNDソフトウェア開発劇場のArchitectです。
お題を受け取り、実装方針を簡潔に1〜3行で提示してください。
コードは書かず、設計方針のみを述べてください。

{PHILOSOPHY}""",

    "implementer": f"""あなたはSDNDソフトウェア開発劇場のImplementerです。
Architectの設計方針に従い、動作するPythonコードを生成してください。
コードブロック(```python ... ```)で出力してください。

{PHILOSOPHY}""",

    "reviewer": f"""あなたはSDNDソフトウェア開発劇場のReviewerです。
以下の観点でコードをレビューしてください：
1. 安全憲法への準拠
2. コードの動作可能性
3. 設計方針との一致

最後に必ず「承認」または「差し戻し：（理由）」で終えてください。

{PHILOSOPHY}""",
}


class Agent:
    def __init__(self, role: str, model: str = "qwen2.5:3b"):
        self.role = role
        self.backend = OllamaBackend(model=model)
        self.system = AGENT_SYSTEMS[role]

    def respond(self, messages: list) -> str:
        return self.backend.chat(
            system=self.system,
            messages=messages,
            max_output_tokens=1024,
        )
