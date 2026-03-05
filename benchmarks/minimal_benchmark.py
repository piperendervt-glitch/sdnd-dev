"""最小ベンチマーク
目的：sdnd-devの性能向上を定量的に測定する

実行例：
  python -m benchmarks.run_benchmark --task 1
  python -m benchmarks.run_benchmark --all
"""

import ast

# ─────────────────────────────────────────
# タスク定義（5問）
# ─────────────────────────────────────────

TASKS = [
    {
        "id": 1,
        "name": "ドキュメント追加",
        "type": "documentation",
        "description": "関数にdocstringを追加せよ",
        "before": """\
def add(a, b):
    return a + b
""",
        "criteria": ["docstring", "param", "return"],
    },
    {
        "id": 2,
        "name": "バグ修正",
        "type": "bugfix",
        "description": "インデックスエラーを修正せよ",
        "before": """\
def get_last(lst):
    return lst[len(lst)]
""",
        "criteria": ["len(lst) - 1", "lst[-1]"],
    },
    {
        "id": 3,
        "name": "ループ最適化",
        "type": "optimization",
        "description": "リスト内包表記を使って最適化せよ",
        "before": """\
def squares(n):
    result = []
    for i in range(n):
        result.append(i * i)
    return result
""",
        "criteria": ["[", "for", "in", "range"],
    },
    {
        "id": 4,
        "name": "変数名改善",
        "type": "naming",
        "description": "変数名をわかりやすくリファクタせよ",
        "before": """\
def calc(x, y, z):
    a = x * y
    b = a + z
    return b
""",
        "criteria": ["price", "tax", "total", "width", "height", "area"],
    },
    {
        "id": 5,
        "name": "エラーハンドリング追加",
        "type": "error_handling",
        "description": "ゼロ除算に対するエラーハンドリングを追加せよ",
        "before": """\
def divide(a, b):
    return a / b
""",
        "criteria": ["ZeroDivisionError", "ValueError", "if b == 0", "if b != 0"],
    },
]


# ─────────────────────────────────────────
# スコアリング関数
# ─────────────────────────────────────────

def score_before(task: dict) -> float:
    """before コードのスコア（常に0.0〜0.3の低スコア）"""
    code = task["before"]
    score = 0.0
    try:
        ast.parse(code)
        score += 0.2
    except SyntaxError:
        pass
    return round(score, 2)


def _score_task1_docstring(after_code: str) -> float:
    """タスク1: ASTベースのdocstring存在チェック"""
    score = 0.0
    try:
        tree = ast.parse(after_code)
    except SyntaxError:
        return 0.0
    score += 0.3  # 構文OK

    # 関数定義からdocstringを取得
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            docstring = ast.get_docstring(node)
            if docstring:
                score += 0.3  # docstring存在
                doc_lower = docstring.lower()
                # パラメータ説明があるか
                if any(kw in doc_lower for kw in ["param", "args", "argument", "parameter", ":param", "(int", "(float", "(number"]):
                    score += 0.2
                # 戻り値説明があるか
                if any(kw in doc_lower for kw in ["return", "result", ":return"]):
                    score += 0.2
            break  # 最初の関数のみ

    return round(min(score, 1.0), 2)


def _score_task4_varnames(after_code: str) -> float:
    """タスク4: 変数名改善 — 引数/ローカル変数を分離して評価"""
    score = 0.0
    try:
        tree = ast.parse(after_code)
    except SyntaxError:
        return 0.0
    score += 0.3  # 構文OK

    single_char_bad = set("abcxyz")
    placeholder_bad = {"tmp", "val", "var", "temp", "foo", "bar"}

    # 引数名とローカル変数名を分離収集
    arg_names = set()
    local_names = set()
    func_names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.arg):
            arg_names.add(node.arg)
        elif isinstance(node, ast.Name) and isinstance(getattr(node, '_parent', None), ast.Store if hasattr(ast, 'Store') else type(None)):
            local_names.add(node.id)
        elif isinstance(node, ast.Name):
            local_names.add(node.id)
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            func_names.add(node.name)

    # ast.Nameでは代入先かどうか区別しにくいので、ast.Assignのtargetsから取得
    local_assigned = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    local_assigned.add(target.id)

    # ローカル変数（引数以外）に1文字/プレースホルダーが残っているか
    bad_local = (local_assigned - arg_names) & (single_char_bad | placeholder_bad)
    bad_args = arg_names & (single_char_bad | placeholder_bad)

    # ローカル変数の評価（0.2）
    if not bad_local:
        score += 0.2
    elif len(bad_local) <= 1:
        score += 0.1

    # 引数名の評価（0.15）
    if not bad_args:
        score += 0.15
    elif len(bad_args) <= 1:
        score += 0.05

    # 関数名が意味ある名前か（calc/func/fn以外）（0.1）
    generic_func = {"calc", "func", "fn", "f", "do", "run", "process"}
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name not in generic_func:
            score += 0.1
            break

    # 変数名の平均文字数が4文字以上（0.1）
    all_user_names = (local_assigned | arg_names) - {"i", "n", "e", "self", "cls"}
    if all_user_names:
        avg_len = sum(len(n) for n in all_user_names) / len(all_user_names)
        if avg_len >= 4:
            score += 0.1

    # 意味のある変数名が使われているか（0.15）
    meaningful = {"price", "tax", "total", "width", "height", "area",
                  "cost", "amount", "sum", "product", "result", "value",
                  "quantity", "rate", "base", "factor", "multiplier",
                  "number", "count", "length", "size", "output", "input"}
    all_names = local_assigned | arg_names | func_names
    matched = all_names & meaningful
    if len(matched) >= 2:
        score += 0.15
    elif len(matched) >= 1:
        score += 0.1

    return round(min(score, 1.0), 2)


def _score_task2_bugfix(after_code: str) -> float:
    """タスク2: バグ修正 — 5観点の部分点制（各0.14点、構文は0.3）"""
    score = 0.0
    # 1. 構文エラーなし
    try:
        tree = ast.parse(after_code)
    except SyntaxError:
        return 0.0
    score += 0.3

    code_lower = after_code.lower()

    # 2. 正しいインデックスアクセス（lst[-1] または len(lst)-1）
    if "lst[-1]" in after_code or "len(lst) - 1" in after_code or "len(lst)-1" in after_code:
        score += 0.14

    # 3. 元のバグ行が消えている（lst[len(lst)] が存在しない）
    if "lst[len(lst)]" not in after_code:
        score += 0.14

    # 4. 関数がリストを引数に取る構造が維持されている
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            if node.args.args:  # 引数が1つ以上ある
                score += 0.14
            break

    # 5. docstringまたはコメントが存在する
    has_docstring = False
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and ast.get_docstring(node):
            has_docstring = True
            break
    if has_docstring or "#" in after_code:
        score += 0.14

    return round(min(score, 1.0), 2)


def _score_task5_error_handling(after_code: str) -> float:
    """タスク5: エラーハンドリング — 5観点の部分点制（各0.14点、構文は0.3）"""
    score = 0.0
    # 1. 構文エラーなし
    try:
        tree = ast.parse(after_code)
    except SyntaxError:
        return 0.0
    score += 0.3

    # 2. try/except ブロックが存在する
    has_try = any(isinstance(node, ast.Try) for node in ast.walk(tree))
    if has_try:
        score += 0.14

    # 3. 具体的な例外クラス（ZeroDivisionError/ValueError）を使っている
    specific_exceptions = {"ZeroDivisionError", "ValueError", "TypeError", "ArithmeticError"}
    found_exception = False
    for node in ast.walk(tree):
        # raise文で具体的な例外を使用
        if isinstance(node, ast.Raise) and node.exc:
            if isinstance(node.exc, ast.Call) and isinstance(node.exc.func, ast.Name):
                if node.exc.func.id in specific_exceptions:
                    found_exception = True
            elif isinstance(node.exc, ast.Name) and node.exc.id in specific_exceptions:
                found_exception = True
        # except節で具体的な例外をキャッチ
        if isinstance(node, ast.ExceptHandler) and node.type:
            if isinstance(node.type, ast.Name) and node.type.id in specific_exceptions:
                found_exception = True
    if found_exception:
        score += 0.14

    # 4. ゼロ除算ケース（b==0 / b!=0）を明示的に処理している
    code_str = after_code
    zero_check = any(pat in code_str for pat in [
        "b == 0", "b==0", "b != 0", "b!=0",
        "b is 0", "not b", "if b:", "if not b",
    ])
    if zero_check:
        score += 0.14

    # 5. エラーメッセージまたはdocstringが存在する
    has_msg = False
    for node in ast.walk(tree):
        # raise Exception("message") のメッセージ
        if isinstance(node, ast.Raise) and node.exc and isinstance(node.exc, ast.Call):
            if node.exc.args:  # メッセージ引数あり
                has_msg = True
        # docstring
        if isinstance(node, ast.FunctionDef) and ast.get_docstring(node):
            has_msg = True
    if has_msg or "#" in after_code:
        score += 0.14

    return round(min(score, 1.0), 2)


def _score_task3_generic(task: dict, after_code: str) -> float:
    """タスク3: 汎用キーワードマッチ（従来方式）"""
    score = 0.0
    try:
        ast.parse(after_code)
        score += 0.3
    except SyntaxError:
        return 0.0

    criteria = task.get("criteria", [])
    if criteria:
        per_point = 0.7 / len(criteria)
        for keyword in criteria:
            if keyword.lower() in after_code.lower():
                score += per_point

    return round(min(score, 1.0), 2)


def score_after(task: dict, after_code: str) -> float:
    """after コードのスコア（0.0〜1.0）— 全タスクAST＋観点別"""
    scorers = {
        1: lambda code: _score_task1_docstring(code),
        2: lambda code: _score_task2_bugfix(code),
        3: lambda code: _score_task3_generic(task, code),
        4: lambda code: _score_task4_varnames(code),
        5: lambda code: _score_task5_error_handling(code),
    }
    scorer = scorers.get(task["id"])
    if scorer:
        return scorer(after_code)
    return _score_task3_generic(task, after_code)


def get_task(task_id: int) -> dict:
    for t in TASKS:
        if t["id"] == task_id:
            return t
    raise ValueError(f"タスクID {task_id} が見つかりません")
