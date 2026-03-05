"""最小ベンチマーク
目的：sdnd-devの性能向上を定量的に測定する

実行例：
  python -m benchmarks.run_benchmark --task 1
  python -m benchmarks.run_benchmark --all
"""

import ast
import io
import json
import re
import tokenize

# ─────────────────────────────────────────
# タスク定義（12問）
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
    {
        "id": 6,
        "name": "PEP8準拠",
        "type": "naming",
        "description": "PEP8に準拠するようリファクタせよ（インデント4スペース、行長79文字以内、snake_case命名）",
        "before": """\
def calculateTotalPrice(itemPrice,taxRate):
  totalBeforeTax=itemPrice*taxRate
  discountedPrice=totalBeforeTax-totalBeforeTax*0.1
  finalMessage="The final price for the item after applying the discount and tax is: "+str(discountedPrice)
  return discountedPrice
""",
        "criteria": ["snake_case"],
    },
    {
        "id": 7,
        "name": "型ヒント追加",
        "type": "documentation",
        "description": "全引数と戻り値に型ヒントを追加し、docstringも付けよ",
        "before": """\
def greet(name, times):
    result = []
    for i in range(times):
        result.append(f"Hello, {name}!")
    return result

def average(numbers):
    return sum(numbers) / len(numbers)
""",
        "criteria": ["->", ":"],
    },
    {
        "id": 8,
        "name": "関数長制限",
        "type": "optimization",
        "description": "50行を超える長い関数を、50行以内の小さな関数に分割せよ",
        "before": """\
def process_data(data):
    result = []
    for item in data:
        if isinstance(item, str):
            item = item.strip()
            if item == "":
                continue
            item = item.lower()
            if item.startswith("#"):
                continue
            parts = item.split(",")
            for part in parts:
                part = part.strip()
                if part == "":
                    continue
                try:
                    num = float(part)
                    result.append(num)
                except ValueError:
                    result.append(part)
        elif isinstance(item, (int, float)):
            if item < 0:
                item = abs(item)
            if item > 1000:
                item = 1000
            result.append(item)
        elif isinstance(item, list):
            for sub in item:
                if isinstance(sub, str):
                    sub = sub.strip().lower()
                    if sub != "":
                        result.append(sub)
                elif isinstance(sub, (int, float)):
                    if sub < 0:
                        sub = abs(sub)
                    result.append(sub)
                else:
                    result.append(str(sub))
        elif isinstance(item, dict):
            for key, value in item.items():
                key = str(key).strip()
                if isinstance(value, (int, float)):
                    result.append(value)
                elif isinstance(value, str):
                    value = value.strip()
                    if value != "":
                        result.append(value)
                else:
                    result.append(str(value))
        else:
            result.append(str(item))
    total = 0
    count = 0
    for r in result:
        if isinstance(r, (int, float)):
            total += r
            count += 1
    if count > 0:
        average = total / count
    else:
        average = 0
    return {"items": result, "total": total, "count": count, "average": average}
""",
        "criteria": ["def ", "return"],
    },
    {
        "id": 9,
        "name": "セキュリティ脆弱性修正",
        "type": "security",
        "description": "eval/execを使った危険なコードを安全な代替実装に修正せよ",
        "before": """\
def calculate(expression):
    return eval(expression)

def run_code(code_string):
    exec(code_string)
    return "executed"

def safe_sum(a, b):
    return eval(f"{a} + {b}")
""",
        "criteria": ["eval", "exec"],
    },
    {
        "id": 10,
        "name": "ユニットテスト自動追加",
        "type": "documentation",
        "description": "テストのない関数にユニットテストを追加せよ",
        "before": """\
def multiply(a, b):
    return a * b
""",
        "criteria": ["assert", "test_", "unittest"],
    },
    {
        "id": 11,
        "name": "ログ出力JSON統一",
        "type": "optimization",
        "description": "print()によるログ出力をJSON形式またはloggingに統一せよ",
        "before": """\
def process(data):
    print("処理開始")
    result = data * 2
    print("処理完了: " + str(result))
    return result
""",
        "criteria": ["json", "logging", "import"],
    },
    {
        "id": 12,
        "name": "ログレベル動的変更",
        "type": "error_handling",
        "description": "ログレベルを引数で動的に変更できるようリファクタせよ。バリデーションとdocstringも追加すること",
        "before": """\
def setup_logger():
    import logging
    logging.basicConfig(level=logging.DEBUG)
    logger = logging.getLogger(__name__)
    return logger
""",
        "criteria": ["setLevel", "logging"],
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

    # 2. 防御パターンが存在する（try/except または 事前チェック if + raise）
    has_try = any(isinstance(node, ast.Try) for node in ast.walk(tree))
    has_guard = any(isinstance(node, ast.If) for node in ast.walk(tree)) and \
                any(isinstance(node, ast.Raise) for node in ast.walk(tree))
    if has_try or has_guard:
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


def _score_task6_pep8(after_code: str) -> float:
    """タスク6(T6): PEP8準拠 — インデント・行長・snake_caseをチェック"""
    score = 0.0
    try:
        tree = ast.parse(after_code)
    except SyntaxError:
        return 0.0
    score += 0.2  # 構文OK

    lines = after_code.splitlines()

    # 1. インデント4スペース（tokenizeで検出）(0.25)
    indent_ok = True
    try:
        tokens = tokenize.generate_tokens(io.StringIO(after_code).readline)
        for tok in tokens:
            if tok.type == tokenize.INDENT:
                indent_str = tok.string
                if indent_str and indent_str != indent_str.replace('\t', '    '):
                    indent_ok = False
                elif indent_str and len(indent_str) % 4 != 0:
                    indent_ok = False
    except tokenize.TokenError:
        pass
    # 2スペースインデントが残っていないか追加チェック
    for line in lines:
        stripped = line.lstrip()
        if stripped and line != stripped:
            leading = len(line) - len(stripped)
            if leading % 4 != 0 and leading % 2 == 0:
                indent_ok = False
                break
    if indent_ok:
        score += 0.25

    # 2. 行長79文字以内 (0.25)
    long_lines = [l for l in lines if len(l) > 79]
    if not long_lines:
        score += 0.25
    elif len(long_lines) <= 1:
        score += 0.1

    # 3. 関数名・変数名がsnake_case (0.3)
    camel_re = re.compile(r'[a-z][A-Z]')
    names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            names.add(node.name)
        if isinstance(node, ast.arg):
            names.add(node.arg)
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    names.add(target.id)

    camel_names = [n for n in names if camel_re.search(n)]
    if not camel_names:
        score += 0.3
    elif len(camel_names) <= 1:
        score += 0.15

    return round(min(score, 1.0), 2)


def _score_task7_type_hints(after_code: str) -> float:
    """タスク7(T7): 型ヒント追加 — 引数・戻り値アノテーション + docstring"""
    score = 0.0
    try:
        tree = ast.parse(after_code)
    except SyntaxError:
        return 0.0
    score += 0.2  # 構文OK

    funcs = [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]
    if not funcs:
        return score

    # 全引数にアノテーションがあるか (0.3)
    total_args = 0
    annotated_args = 0
    for func in funcs:
        for arg in func.args.args:
            if arg.arg == "self":
                continue
            total_args += 1
            if arg.annotation is not None:
                annotated_args += 1

    if total_args > 0:
        ratio = annotated_args / total_args
        if ratio >= 1.0:
            score += 0.3
        elif ratio >= 0.5:
            score += 0.15

    # 戻り値アノテーションがあるか (0.25)
    funcs_with_return = sum(1 for f in funcs if f.returns is not None)
    if funcs_with_return == len(funcs):
        score += 0.25
    elif funcs_with_return > 0:
        score += 0.1

    # docstringが存在するか (0.25)
    funcs_with_doc = sum(1 for f in funcs if ast.get_docstring(f))
    if funcs_with_doc == len(funcs):
        score += 0.25
    elif funcs_with_doc > 0:
        score += 0.1

    return round(min(score, 1.0), 2)


def _score_task8_function_length(after_code: str) -> float:
    """タスク8(T8): 関数長制限 — 関数が50行以内か、分割されているか"""
    score = 0.0
    try:
        tree = ast.parse(after_code)
    except SyntaxError:
        return 0.0
    score += 0.2  # 構文OK

    funcs = [node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]

    if not funcs:
        return score

    # 関数が複数に分割されているか
    if len(funcs) >= 2:
        score += 0.3  # 分割ボーナス

    # 各関数が50行以内か
    all_short = True
    for func in funcs:
        func_lines = func.end_lineno - func.lineno + 1 if hasattr(func, 'end_lineno') and func.end_lineno else len(after_code.splitlines())
        if func_lines > 50:
            all_short = False

    if all_short:
        score += 0.3  # 全関数50行以内

    # 元の機能が維持されているか（returnがあるか）
    has_return = any(isinstance(node, ast.Return) for node in ast.walk(tree))
    if has_return:
        score += 0.2

    return round(min(score, 1.0), 2)


def _score_task9_security(after_code: str) -> float:
    """タスク9(T10): セキュリティ脆弱性修正 — eval/execが除去されているか"""
    score = 0.0
    try:
        tree = ast.parse(after_code)
    except SyntaxError:
        return 0.0
    score += 0.2  # 構文OK

    # ASTでeval/exec呼び出しを検出
    dangerous_calls = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            if node.func.id in ("eval", "exec"):
                dangerous_calls.append(node.func.id)

    # eval/execが完全に除去されている
    if not dangerous_calls:
        score += 0.4

    # 安全な代替実装があるか（関数定義が維持されている）
    func_defs = [node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]
    if len(func_defs) >= 2:
        score += 0.2  # 元の関数構造が維持されている

    # 安全なパターンが使われているか（int/float変換、ast.literal_eval、operator等）
    safe_patterns = ["int(", "float(", "ast.literal_eval", "operator", "isinstance", "try:", "except"]
    safe_count = sum(1 for p in safe_patterns if p in after_code)
    if safe_count >= 2:
        score += 0.2
    elif safe_count >= 1:
        score += 0.1

    return round(min(score, 1.0), 2)


def _score_task10_unittest(after_code: str) -> float:
    """タスク10: ユニットテスト自動追加 — テスト関数・assert・正常系異常系"""
    score = 0.0
    try:
        tree = ast.parse(after_code)
    except SyntaxError:
        return 0.0
    score += 0.2  # 構文OK

    # 1. unittest または assert が存在する (0.2)
    has_assert = any(isinstance(node, ast.Assert) for node in ast.walk(tree))
    has_unittest_import = "import unittest" in after_code
    # assertEqual等のメソッド呼び出しもassert扱い
    has_assert_method = any(
        isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
        and node.func.attr.startswith("assert")
        for node in ast.walk(tree)
    )
    if has_assert or has_unittest_import or has_assert_method:
        score += 0.2

    # 2. test_で始まるテスト関数が存在する (0.25)
    test_funcs = [
        node for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef) and node.name.startswith("test_")
    ]
    if test_funcs:
        score += 0.25

    # 3. 元の関数が維持されている (0.1)
    all_funcs = [node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]
    non_test_funcs = [f for f in all_funcs if not f.name.startswith("test_")]
    if non_test_funcs:
        score += 0.1

    # 4. 正常系・異常系のテストケースが含まれる (0.25)
    # 複数のテスト関数 or 複数のassert = 正常系+異常系
    assert_count = sum(1 for node in ast.walk(tree) if isinstance(node, ast.Assert))
    assert_method_count = sum(
        1 for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
        and node.func.attr.startswith("assert")
    )
    total_assertions = assert_count + assert_method_count
    if total_assertions >= 3 or len(test_funcs) >= 2:
        score += 0.25
    elif total_assertions >= 2:
        score += 0.15

    return round(min(score, 1.0), 2)


def _score_task11_json_logging(after_code: str) -> float:
    """タスク11: ログ出力JSON統一 — print除去・json/logging使用"""
    score = 0.0
    try:
        tree = ast.parse(after_code)
    except SyntaxError:
        return 0.0
    score += 0.2  # 構文OK

    # 1. import json または import logging が存在する (0.25)
    has_json_import = any(
        isinstance(node, ast.Import) and any(alias.name == "json" for alias in node.names)
        for node in ast.walk(tree)
    ) or any(
        isinstance(node, ast.ImportFrom) and node.module == "json"
        for node in ast.walk(tree)
    )
    has_logging_import = any(
        isinstance(node, ast.Import) and any(alias.name == "logging" for alias in node.names)
        for node in ast.walk(tree)
    ) or any(
        isinstance(node, ast.ImportFrom) and node.module == "logging"
        for node in ast.walk(tree)
    )
    if has_json_import or has_logging_import:
        score += 0.25

    # 2. print()が除去されている (0.3)
    print_calls = [
        node for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
        and node.func.id == "print"
    ]
    if not print_calls:
        score += 0.3
    elif len(print_calls) <= 1:
        score += 0.1

    # 3. JSON形式の出力またはlogging使用が確認できる (0.25)
    has_json_dumps = any(
        isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
        and node.func.attr == "dumps"
        for node in ast.walk(tree)
    )
    has_logging_call = any(
        isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
        and node.func.attr in ("info", "debug", "warning", "error", "critical")
        for node in ast.walk(tree)
    )
    if has_json_dumps or has_logging_call:
        score += 0.25

    return round(min(score, 1.0), 2)


def zero_from_generate_eval(after_code: str) -> float:
    """beforeコードが不要なタスク（創造性系・リファクタ系）のスコアリング関数。

    評価観点（各0.25点）：
    1. 関数名がsnake_caseで意味のある名前か
    2. docstringが存在するか
    3. 引数に型ヒントがあるか
    4. PEP8準拠（行長・インデント）
    """
    score = 0.0
    try:
        tree = ast.parse(after_code)
    except SyntaxError:
        return 0.0

    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            # 1. snake_case チェック
            if re.match(r'^[a-z][a-z0-9_]*$', node.name):
                score += 0.25
            # 2. docstring チェック
            if ast.get_docstring(node):
                score += 0.25
            # 3. 型ヒントチェック
            if node.returns or any(arg.annotation for arg in node.args.args):
                score += 0.25
            break

    # 4. PEP8行長チェック
    lines = after_code.split('\n')
    if all(len(line) <= 79 for line in lines):
        score += 0.25

    return round(min(score, 1.0), 2)


def _score_task12_log_level(after_code: str) -> float:
    """タスク12(T15): ログレベル動的変更 — setLevel/引数/バリデーション/docstring"""
    score = 0.0
    try:
        tree = ast.parse(after_code)
    except SyntaxError:
        return 0.0
    score += 0.1  # 構文OK

    # 1. logging.setLevel() の使用 (0.25)
    has_set_level = any(
        isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
        and node.func.attr == "setLevel"
        for node in ast.walk(tree)
    )
    if has_set_level:
        score += 0.25

    # 2. 引数でログレベルを受け取る設計 (0.25)
    funcs = [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]
    has_level_arg = False
    for func in funcs:
        for arg in func.args.args:
            if arg.arg in ("level", "log_level", "loglevel"):
                has_level_arg = True
        # デフォルト引数でもOK
        if func.args.defaults:
            has_level_arg = True
    if has_level_arg:
        score += 0.25

    # 3. try/except または if によるバリデーション (0.2)
    has_try = any(isinstance(node, ast.Try) for node in ast.walk(tree))
    has_if = any(isinstance(node, ast.If) for node in ast.walk(tree))
    if has_try or has_if:
        score += 0.2

    # 4. docstring の存在 (0.2)
    has_docstring = any(
        isinstance(node, ast.FunctionDef) and ast.get_docstring(node)
        for node in ast.walk(tree)
    )
    if has_docstring:
        score += 0.2

    return round(min(score, 1.0), 2)


def score_after(task: dict, after_code: str) -> float:
    """after コードのスコア（0.0〜1.0）— 全タスクAST＋観点別"""
    scorers = {
        1: lambda code: _score_task1_docstring(code),
        2: lambda code: _score_task2_bugfix(code),
        3: lambda code: _score_task3_generic(task, code),
        4: lambda code: _score_task4_varnames(code),
        5: lambda code: _score_task5_error_handling(code),
        6: lambda code: _score_task6_pep8(code),
        7: lambda code: _score_task7_type_hints(code),
        8: lambda code: _score_task8_function_length(code),
        9: lambda code: _score_task9_security(code),
        10: lambda code: _score_task10_unittest(code),
        11: lambda code: _score_task11_json_logging(code),
        12: lambda code: _score_task12_log_level(code),
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


def format_benchmark_results(results):
    """ベンチマーク結果を受け取りJSON形式の文字列として返す。

    Args:
        results: 辞書のリスト（例: [{'task': 'T1', 'score': 1.00}, ...]）
    Returns:
        JSON形式の文字列
    """
    return json.dumps(results, ensure_ascii=False, indent=4)
