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
# タスク定義（25問）
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
    {
        "id": 15,
        "name": "クラスを関数に分割",
        "type": "optimization",
        "description": "クラスを廃止して独立した関数に分割せよ。docstringも追加すること",
        "before": """\
class Calculator:
    def add(self, a, b):
        return a + b
    def multiply(self, a, b):
        return a * b
""",
        "criteria": ["def", "return"],
    },
    {
        "id": 14,
        "name": "設定文字列パース関数",
        "type": "error_handling",
        "description": "設定文字列をパースする関数にエラー処理・型変換・docstringを追加せよ",
        "before": """\
def parse_config(config_str):
    result = {}
    for line in config_str.split('\\n'):
        key, value = line.split('=')
        result[key] = value
    return result
""",
        "criteria": ["try", "except", "return", "docstring"],
    },
    {
        "id": 13,
        "name": "import文の整理・不要削除",
        "type": "optimization",
        "description": "未使用のimport文を削除し、必要なimportのみ残せ。関数の動作は変えないこと",
        "before": """\
import os
import sys
import json
import re
import math

def greet(name):
    return "Hello, " + name
""",
        "criteria": ["import", "def", "return"],
    },
    {
        "id": 16,
        "name": "三項演算子への置き換え",
        "type": "optimization",
        "description": "冗長なif-elseを三項演算子（条件式）に置き換えよ。docstringも追加すること",
        "before": """\
def check_age(age):
    if age >= 18:
        status = "adult"
    else:
        status = "minor"
    return status
""",
        "criteria": ["if", "else", "return"],
    },
    {
        "id": 17,
        "name": "argparseの使用",
        "type": "optimization",
        "description": "手動の引数解析をargparseに書き換えよ。docstringも追加すること",
        "before": """\
def parse_args(args):
    host = "localhost"
    port = 8080
    for arg in args:
        if arg.startswith("--host="):
            host = arg.split("=")[1]
        if arg.startswith("--port="):
            port = int(arg.split("=")[1])
    return host, port
""",
        "criteria": ["argparse", "add_argument"],
    },
    {
        "id": 18,
        "name": "try-exceptでデフォルト値",
        "type": "error_handling",
        "description": "例外時にデフォルト値を返すようにエラーハンドリングを追加せよ。docstringも追加すること",
        "before": """\
def safe_int(value):
    return int(value)
""",
        "criteria": ["try", "except", "return"],
    },
    {
        "id": 19,
        "name": "ジェネレータ関数への変換",
        "type": "optimization",
        "description": "リスト蓄積パターンをyieldを使ったジェネレータ関数に変換せよ。docstringも追加すること",
        "before": """\
def get_even_numbers(numbers):
    result = []
    for n in numbers:
        if n % 2 == 0:
            result.append(n)
    return result
""",
        "criteria": ["yield", "def"],
    },
    {
        "id": 20,
        "name": "デコレータを使った処理共通化",
        "type": "optimization",
        "description": "重複するprint処理をデコレータで共通化せよ。docstringも追加すること",
        "before": """\
def add(a, b):
    print("calling add")
    result = a + b
    print(f"result: {result}")
    return result

def multiply(a, b):
    print("calling multiply")
    result = a * b
    print(f"result: {result}")
    return result
""",
        "criteria": ["def", "@", "wrapper"],
    },
    {
        "id": 21,
        "name": "辞書内包表記への変換",
        "type": "optimization",
        "description": "forループによる辞書構築を辞書内包表記に変換せよ。docstringも追加すること",
        "before": """\
def make_squares_dict(numbers):
    result = {}
    for n in numbers:
        result[n] = n * n
    return result
""",
        "criteria": ["{", "for", "in", ":"],
    },
    {
        "id": 22,
        "name": "ガード節（早期リターン）",
        "type": "optimization",
        "description": "深いネストをガード節（早期リターン）でフラットにせよ。docstringも追加すること",
        "before": """\
def process_order(order):
    if order is not None:
        if order.get("quantity") > 0:
            if order.get("price") > 0:
                total = order["quantity"] * order["price"]
                return total
            else:
                return 0
        else:
            return 0
    else:
        return 0
""",
        "criteria": ["return", "if"],
    },
    {
        "id": 23,
        "name": "プロパティデコレータ追加",
        "type": "documentation",
        "description": "get_メソッドを@propertyデコレータに変換せよ。docstringも追加すること",
        "before": """\
class Circle:
    def __init__(self, radius):
        self.radius = radius
    def get_area(self):
        return 3.14159 * self.radius ** 2
    def get_circumference(self):
        return 2 * 3.14159 * self.radius
""",
        "criteria": ["@property", "def area", "def circumference"],
    },
    {
        "id": 24,
        "name": "ログフォーマットカスタマイズ",
        "type": "error_handling",
        "description": "ログフォーマットを引数で変更可能にせよ。タイムスタンプ・レベル対応。docstringも追加すること",
        "before": """\
def format_log(message):
    return "[LOG] " + message
""",
        "criteria": ["format", "return", "def"],
    },
    {
        "id": 25,
        "name": "enumerate使用への変換",
        "type": "optimization",
        "description": "手動インデックス管理をenumerateに変換せよ。docstringも追加すること",
        "before": """\
def index_items(items):
    result = []
    i = 0
    for item in items:
        result.append(f"{i}: {item}")
        i += 1
    return result
""",
        "criteria": ["enumerate", "for", "return"],
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


def _score_task14_config_parse(after_code: str) -> float:
    """タスク14(T14): 設定文字列パース — 例外処理・dict返却・docstring・型変換"""
    score = 0.0
    try:
        tree = ast.parse(after_code)
    except SyntaxError:
        return 0.0
    score += 0.2  # 構文OK

    # 1. try/exceptが存在する (0.25)
    has_try = any(isinstance(node, ast.Try) for node in ast.walk(tree))
    if has_try:
        score += 0.25

    # 2. dictを返している（return文が存在する）(0.15)
    has_return = any(isinstance(node, ast.Return) for node in ast.walk(tree))
    if has_return:
        score += 0.15

    # 3. docstringが存在する (0.2)
    has_docstring = any(
        isinstance(node, ast.FunctionDef) and ast.get_docstring(node)
        for node in ast.walk(tree)
    )
    if has_docstring:
        score += 0.2

    # 4. 値の型変換処理がある（int()/float()/strip()等の呼び出し）(0.2)
    type_convert_funcs = {"int", "float", "bool", "str"}
    strip_methods = {"strip", "lstrip", "rstrip", "lower", "upper"}
    has_type_convert = False
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            # int(), float() 等の組み込み関数
            if isinstance(node.func, ast.Name) and node.func.id in type_convert_funcs:
                has_type_convert = True
            # .strip() 等のメソッド呼び出し
            if isinstance(node.func, ast.Attribute) and node.func.attr in strip_methods:
                has_type_convert = True
    if has_type_convert:
        score += 0.2

    return round(min(score, 1.0), 2)


def _score_task15_class_to_functions(after_code: str) -> float:
    """タスク15(T13): クラスを関数に分割 — ClassDef除去・FunctionDef2個以上・docstring"""
    score = 0.0
    try:
        tree = ast.parse(after_code)
    except SyntaxError:
        return 0.0
    score += 0.2  # 構文OK

    # 1. ClassDefが存在しない (0.3)
    has_class = any(isinstance(node, ast.ClassDef) for node in ast.walk(tree))
    if not has_class:
        score += 0.3

    # 2. トップレベルのFunctionDefが2個以上 (0.25)
    top_funcs = [node for node in ast.iter_child_nodes(tree) if isinstance(node, ast.FunctionDef)]
    if len(top_funcs) >= 2:
        score += 0.25
    elif len(top_funcs) >= 1:
        score += 0.1

    # 3. docstringが存在する (0.25)
    has_docstring = any(
        isinstance(node, ast.FunctionDef) and ast.get_docstring(node)
        for node in ast.walk(tree)
    )
    if has_docstring:
        score += 0.25

    return round(min(score, 1.0), 2)


def _score_task13_unused_imports(after_code: str) -> float:
    """タスク13(T16): import文整理 — 未使用importが除去されているか"""
    score = 0.0
    try:
        tree = ast.parse(after_code)
    except SyntaxError:
        return 0.0
    score += 0.2  # 構文OK

    # 収集: import されたモジュール名
    imported_names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imported_names.add(alias.asname or alias.name)
        elif isinstance(node, ast.ImportFrom):
            for alias in node.names:
                imported_names.add(alias.asname or alias.name)

    # 収集: 関数本体等で実際に使われている名前
    used_names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            used_names.add(node.id)
        elif isinstance(node, ast.Attribute):
            # os.path のような使い方
            if isinstance(node.value, ast.Name):
                used_names.add(node.value.id)

    # 未使用import = importされたが使われていない名前
    unused = imported_names - used_names
    # beforeの未使用: os, sys, json, re, math (5個)
    before_unused = {"os", "sys", "json", "re", "math"}

    # 1. 未使用importが除去されている (0.35)
    if not unused:
        score += 0.35
    elif len(unused) <= 1:
        score += 0.15

    # 2. beforeにあった未使用importが減っている (0.15)
    remaining_bad = imported_names & before_unused - used_names
    if len(remaining_bad) == 0:
        score += 0.15
    elif len(remaining_bad) <= 2:
        score += 0.05

    # 3. 関数の動作が維持されている（returnが存在する）(0.15)
    has_return = any(isinstance(node, ast.Return) for node in ast.walk(tree))
    if has_return:
        score += 0.15

    # 4. docstringが追加されている (0.15)
    has_docstring = any(
        isinstance(node, ast.FunctionDef) and ast.get_docstring(node)
        for node in ast.walk(tree)
    )
    if has_docstring:
        score += 0.15

    return round(min(score, 1.0), 2)


def _score_task16_ternary(after_code: str) -> float:
    """タスク16(T17): 三項演算子 — IfExpの使用・簡潔さ"""
    score = 0.0
    try:
        tree = ast.parse(after_code)
    except SyntaxError:
        return 0.0
    score += 0.2

    # 1. ast.IfExp（三項演算子）が使われている (0.35)
    has_ifexp = any(isinstance(node, ast.IfExp) for node in ast.walk(tree))
    if has_ifexp:
        score += 0.35

    # 2. 関数が維持されている (0.1)
    has_func = any(isinstance(node, ast.FunctionDef) for node in ast.walk(tree))
    if has_func:
        score += 0.1

    # 3. returnが存在する (0.1)
    has_return = any(isinstance(node, ast.Return) for node in ast.walk(tree))
    if has_return:
        score += 0.1

    # 4. docstringが存在する (0.25)
    has_docstring = any(
        isinstance(node, ast.FunctionDef) and ast.get_docstring(node)
        for node in ast.walk(tree)
    )
    if has_docstring:
        score += 0.25

    return round(min(score, 1.0), 2)


def _score_task17_argparse(after_code: str) -> float:
    """タスク17(T18): argparse使用"""
    score = 0.0
    try:
        tree = ast.parse(after_code)
    except SyntaxError:
        return 0.0
    score += 0.2

    # 1. import argparse (0.25)
    has_argparse = "argparse" in after_code
    if has_argparse:
        score += 0.25

    # 2. add_argument呼び出し (0.25)
    has_add_arg = "add_argument" in after_code
    if has_add_arg:
        score += 0.25

    # 3. docstringが存在する (0.15)
    has_docstring = any(
        isinstance(node, ast.FunctionDef) and ast.get_docstring(node)
        for node in ast.walk(tree)
    )
    if has_docstring:
        score += 0.15

    # 4. parse_args呼び出し (0.15)
    has_parse = "parse_args" in after_code
    if has_parse:
        score += 0.15

    return round(min(score, 1.0), 2)


def _score_task18_default_value(after_code: str) -> float:
    """タスク18(T19): try-exceptでデフォルト値"""
    score = 0.0
    try:
        tree = ast.parse(after_code)
    except SyntaxError:
        return 0.0
    score += 0.2

    # 1. try/exceptが存在する (0.3)
    has_try = any(isinstance(node, ast.Try) for node in ast.walk(tree))
    if has_try:
        score += 0.3

    # 2. 具体的な例外クラス (0.15)
    specific = {"ValueError", "TypeError", "Exception"}
    found = any(
        isinstance(node, ast.ExceptHandler) and node.type
        and isinstance(node.type, ast.Name) and node.type.id in specific
        for node in ast.walk(tree)
    )
    if found:
        score += 0.15

    # 3. returnが2つ以上（正常系+デフォルト値） (0.15)
    returns = sum(1 for node in ast.walk(tree) if isinstance(node, ast.Return))
    if returns >= 2:
        score += 0.15

    # 4. docstringが存在する (0.2)
    has_docstring = any(
        isinstance(node, ast.FunctionDef) and ast.get_docstring(node)
        for node in ast.walk(tree)
    )
    if has_docstring:
        score += 0.2

    return round(min(score, 1.0), 2)


def _score_task19_generator(after_code: str) -> float:
    """タスク19(T20): ジェネレータ関数"""
    score = 0.0
    try:
        tree = ast.parse(after_code)
    except SyntaxError:
        return 0.0
    score += 0.2

    # 1. yieldが使われている (0.35)
    has_yield = any(isinstance(node, (ast.Yield, ast.YieldFrom)) for node in ast.walk(tree))
    if has_yield:
        score += 0.35

    # 2. リスト蓄積パターンが除去されている（append無し） (0.15)
    has_append = any(
        isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
        and node.func.attr == "append"
        for node in ast.walk(tree)
    )
    if not has_append:
        score += 0.15

    # 3. 関数が維持されている (0.1)
    has_func = any(isinstance(node, ast.FunctionDef) for node in ast.walk(tree))
    if has_func:
        score += 0.1

    # 4. docstringが存在する (0.2)
    has_docstring = any(
        isinstance(node, ast.FunctionDef) and ast.get_docstring(node)
        for node in ast.walk(tree)
    )
    if has_docstring:
        score += 0.2

    return round(min(score, 1.0), 2)


def _score_task20_decorator(after_code: str) -> float:
    """タスク20(T21): デコレータを使った処理共通化"""
    score = 0.0
    try:
        tree = ast.parse(after_code)
    except SyntaxError:
        return 0.0
    score += 0.2

    # 1. デコレータ付き関数がある (0.3)
    has_decorator = any(
        isinstance(node, ast.FunctionDef) and node.decorator_list
        for node in ast.walk(tree)
    )
    if has_decorator:
        score += 0.3

    # 2. wrapper/inner関数パターン（ネストした関数定義） (0.2)
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            inner_funcs = [n for n in ast.walk(node) if isinstance(n, ast.FunctionDef) and n is not node]
            if inner_funcs:
                score += 0.2
                break

    # 3. 元の関数（add, multiply）が維持されている (0.15)
    func_names = {n.name for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)}
    if "add" in func_names and "multiply" in func_names:
        score += 0.15

    # 4. docstringが存在する (0.15)
    has_docstring = any(
        isinstance(node, ast.FunctionDef) and ast.get_docstring(node)
        for node in ast.walk(tree)
    )
    if has_docstring:
        score += 0.15

    return round(min(score, 1.0), 2)


def _score_task21_dict_comprehension(after_code: str) -> float:
    """タスク21(T22): 辞書内包表記"""
    score = 0.0
    try:
        tree = ast.parse(after_code)
    except SyntaxError:
        return 0.0
    score += 0.2

    # 1. DictComp（辞書内包表記）が使われている (0.35)
    has_dictcomp = any(isinstance(node, ast.DictComp) for node in ast.walk(tree))
    if has_dictcomp:
        score += 0.35

    # 2. forループによる蓄積が除去されている (0.15)
    has_for_assign = False
    for node in ast.walk(tree):
        if isinstance(node, ast.For):
            for child in ast.walk(node):
                if isinstance(child, ast.Subscript):
                    has_for_assign = True
    if not has_for_assign:
        score += 0.15

    # 3. returnが存在する (0.1)
    has_return = any(isinstance(node, ast.Return) for node in ast.walk(tree))
    if has_return:
        score += 0.1

    # 4. docstringが存在する (0.2)
    has_docstring = any(
        isinstance(node, ast.FunctionDef) and ast.get_docstring(node)
        for node in ast.walk(tree)
    )
    if has_docstring:
        score += 0.2

    return round(min(score, 1.0), 2)


def _score_task22_guard_clause(after_code: str) -> float:
    """タスク22(T23): ガード節（早期リターン）"""
    score = 0.0
    try:
        tree = ast.parse(after_code)
    except SyntaxError:
        return 0.0
    score += 0.2

    # 1. 関数が維持されている (0.1)
    funcs = [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]
    if funcs:
        score += 0.1

    # 2. 早期リターン（returnが複数ある） (0.2)
    returns = sum(1 for n in ast.walk(tree) if isinstance(n, ast.Return))
    if returns >= 2:
        score += 0.2

    # 3. ネストが浅い（If内にIfが3段以上ない） (0.25)
    max_depth = 0
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            depth = _if_depth(node)
            max_depth = max(max_depth, depth)
    if max_depth <= 2:
        score += 0.25
    elif max_depth <= 3:
        score += 0.1

    # 4. docstringが存在する (0.25)
    has_docstring = any(
        isinstance(node, ast.FunctionDef) and ast.get_docstring(node)
        for node in ast.walk(tree)
    )
    if has_docstring:
        score += 0.25

    return round(min(score, 1.0), 2)


def _if_depth(node, current=0):
    """If文のネスト深度を計測するヘルパー"""
    max_d = current
    for child in ast.iter_child_nodes(node):
        if isinstance(child, ast.If):
            d = _if_depth(child, current + 1)
            max_d = max(max_d, d)
        else:
            d = _if_depth(child, current)
            max_d = max(max_d, d)
    return max_d


def _score_task23_property(after_code: str) -> float:
    """タスク23(T24): プロパティデコレータ"""
    score = 0.0
    try:
        tree = ast.parse(after_code)
    except SyntaxError:
        return 0.0
    score += 0.2

    # 1. @propertyデコレータが使われている (0.3)
    has_property = False
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.decorator_list:
            for dec in node.decorator_list:
                if isinstance(dec, ast.Name) and dec.id == "property":
                    has_property = True
    if has_property:
        score += 0.3

    # 2. get_プレフィックスのメソッドが除去されている (0.2)
    func_names = {n.name for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)}
    if "get_area" not in func_names and "get_circumference" not in func_names:
        score += 0.2
    elif "get_area" not in func_names or "get_circumference" not in func_names:
        score += 0.1

    # 3. クラスが維持されている (0.1)
    has_class = any(isinstance(node, ast.ClassDef) for node in ast.walk(tree))
    if has_class:
        score += 0.1

    # 4. docstringが存在する (0.2)
    has_docstring = any(
        isinstance(node, (ast.FunctionDef, ast.ClassDef)) and ast.get_docstring(node)
        for node in ast.walk(tree)
    )
    if has_docstring:
        score += 0.2

    return round(min(score, 1.0), 2)


def _score_task24_log_format(after_code: str) -> float:
    """タスク24(T25): ログフォーマットカスタマイズ"""
    score = 0.0
    try:
        tree = ast.parse(after_code)
    except SyntaxError:
        return 0.0
    score += 0.2

    # 1. 引数が追加されている（level, format等） (0.25)
    funcs = [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]
    has_extra_args = False
    for func in funcs:
        if len(func.args.args) >= 2 or func.args.defaults:
            has_extra_args = True
    if has_extra_args:
        score += 0.25

    # 2. f-string/formatが使われている (0.15)
    has_format = any(isinstance(node, ast.JoinedStr) for node in ast.walk(tree))
    if has_format or "format" in after_code or "strftime" in after_code:
        score += 0.15

    # 3. returnが存在する (0.15)
    has_return = any(isinstance(node, ast.Return) for node in ast.walk(tree))
    if has_return:
        score += 0.15

    # 4. docstringが存在する (0.25)
    has_docstring = any(
        isinstance(node, ast.FunctionDef) and ast.get_docstring(node)
        for node in ast.walk(tree)
    )
    if has_docstring:
        score += 0.25

    return round(min(score, 1.0), 2)


def _score_task25_enumerate(after_code: str) -> float:
    """タスク25(T25): enumerate使用"""
    score = 0.0
    try:
        tree = ast.parse(after_code)
    except SyntaxError:
        return 0.0
    score += 0.2

    # 1. enumerateが使われている (0.35)
    has_enumerate = any(
        isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
        and node.func.id == "enumerate"
        for node in ast.walk(tree)
    )
    if has_enumerate:
        score += 0.35

    # 2. 手動カウンタ(i = 0, i += 1)が除去されている (0.15)
    has_manual_counter = "i = 0" in after_code or "i += 1" in after_code or "i+=1" in after_code
    if not has_manual_counter:
        score += 0.15

    # 3. returnが存在する (0.1)
    has_return = any(isinstance(node, ast.Return) for node in ast.walk(tree))
    if has_return:
        score += 0.1

    # 4. docstringが存在する (0.2)
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
        13: lambda code: _score_task13_unused_imports(code),
        14: lambda code: _score_task14_config_parse(code),
        15: lambda code: _score_task15_class_to_functions(code),
        16: lambda code: _score_task16_ternary(code),
        17: lambda code: _score_task17_argparse(code),
        18: lambda code: _score_task18_default_value(code),
        19: lambda code: _score_task19_generator(code),
        20: lambda code: _score_task20_decorator(code),
        21: lambda code: _score_task21_dict_comprehension(code),
        22: lambda code: _score_task22_guard_clause(code),
        23: lambda code: _score_task23_property(code),
        24: lambda code: _score_task24_log_format(code),
        25: lambda code: _score_task25_enumerate(code),
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
