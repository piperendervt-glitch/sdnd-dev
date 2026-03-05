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
# タスク定義（51問：リファクタ35問 + HumanEval 8問 + HumanEval-Pure 8問）
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
    # ── 劇場・RP特化系 ──
    {
        "id": 26,
        "name": "シナリオテンプレート生成",
        "type": "theater",
        "description": "劇場のシナリオテンプレートを生成する関数を書き換えよ。場面（scene）・登場人物（characters）・セリフ（dialogue）を辞書で返す構造にすること。docstringも追加すること",
        "before": """\
def create_scenario():
    return "Scene 1: Hello"
""",
        "criteria": ["scene", "characters", "dialogue", "dict", "return"],
    },
    {
        "id": 27,
        "name": "キャラクター設定パーサー",
        "type": "theater",
        "description": "キャラクター設定の文字列を辞書に変換するパーサーを改善せよ。name/role/traitの3フィールドをパースし、不正入力時はValueErrorを出すこと。docstringも追加すること",
        "before": """\
def parse_character(text):
    parts = text.split(",")
    return parts[0], parts[1], parts[2]
""",
        "criteria": ["dict", "name", "role", "ValueError"],
    },
    {
        "id": 28,
        "name": "セリフフォーマッター",
        "type": "theater",
        "description": "セリフを台本形式（'名前: 「セリフ」'）にフォーマットする関数を改善せよ。空文字列チェック、複数セリフ対応（リスト入力）を追加すること。docstringも追加すること",
        "before": """\
def format_dialogue(name, line):
    return name + ": " + line
""",
        "criteria": ["format", "return", "def"],
    },
    # ── 実務的・日常的系 ──
    {
        "id": 29,
        "name": "CSV→辞書変換",
        "type": "practical",
        "description": "CSVテキストを辞書のリストに変換する関数を改善せよ。csvモジュールまたは適切なパースを使用し、ヘッダー行をキーにすること。docstringも追加すること",
        "before": """\
def parse_csv(text):
    lines = text.split("\\n")
    result = []
    for line in lines:
        result.append(line.split(","))
    return result
""",
        "criteria": ["csv", "dict", "return"],
    },
    {
        "id": 30,
        "name": "日付フォーマット統一",
        "type": "practical",
        "description": "文字列連結の日付フォーマットをdatetimeモジュールを使った安全な実装に書き換えよ。docstringも追加すること",
        "before": """\
def format_date(year, month, day):
    return str(year) + "/" + str(month) + "/" + str(day)
""",
        "criteria": ["datetime", "strftime", "return"],
    },
    {
        "id": 31,
        "name": "リトライデコレータ",
        "type": "practical",
        "description": "手動リトライコードをデコレータパターンにリファクタせよ。最大リトライ回数を引数で指定可能にすること。docstringも追加すること",
        "before": """\
def fetch_data(url):
    import urllib.request
    for i in range(3):
        try:
            return urllib.request.urlopen(url).read()
        except Exception:
            if i == 2:
                raise
""",
        "criteria": ["def", "@", "wrapper", "retry"],
    },
    {
        "id": 32,
        "name": "バリデーション関数",
        "type": "practical",
        "description": "入力バリデーションを追加せよ。型チェック（isinstance）、範囲チェック、エラーメッセージ付きのValueErrorを使うこと。docstringも追加すること",
        "before": """\
def register_user(name, age, email):
    return {"name": name, "age": age, "email": email}
""",
        "criteria": ["isinstance", "ValueError", "return"],
    },
    # ── 創造性・人間らしさ系 ──
    {
        "id": 33,
        "name": "エラーメッセージ改善",
        "type": "creative",
        "description": "冷たいエラーメッセージを親切で具体的なメッセージに書き換えよ。ユーザーが次に何をすべきかの提案を含めること。docstringも追加すること",
        "before": """\
def validate_input(value):
    if not value:
        raise ValueError("Error: invalid")
    if not isinstance(value, str):
        raise TypeError("Error: wrong type")
    if len(value) > 100:
        raise ValueError("Error: too long")
    return value
""",
        "criteria": ["raise", "ValueError", "return"],
    },
    {
        "id": 34,
        "name": "挨拶文生成",
        "type": "creative",
        "description": "時間帯に応じた挨拶文を生成する関数に改善せよ。朝/昼/夕/夜を判定し、名前を含むパーソナライズされた挨拶を返すこと。docstringも追加すること",
        "before": """\
def greet():
    return "Hello"
""",
        "criteria": ["datetime", "return", "def"],
    },
    {
        "id": 35,
        "name": "ヘルプテキスト改善",
        "type": "creative",
        "description": "最小限のヘルプ表示を、セクション分け・使用例・オプション説明を含む読みやすいヘルプテキストに改善せよ。docstringも追加すること",
        "before": """\
def show_help():
    print("Usage: tool [options]")
    print("Options: --help, --version")
""",
        "criteria": ["def", "return", "usage", "example"],
    },
    # ── HumanEval系（コード生成 + テストケース通過率）──
    {
        "id": 36,
        "name": "HE: Two Sum",
        "type": "humaneval",
        "description": (
            "リストと目標値を受け取り、合計が目標値になる2つのインデックスを返す関数を実装せよ。\n"
            "答えが必ず1つ存在すると仮定してよい。同じ要素を2回使ってはいけない。\n\n"
            "例:\n"
            "  two_sum([2, 7, 11, 15], 9) -> [0, 1]  # 2+7=9\n"
            "  two_sum([3, 2, 4], 6) -> [1, 2]  # 2+4=6\n"
            "  two_sum([3, 3], 6) -> [0, 1]  # 3+3=6"
        ),
        "before": """\
def two_sum(nums, target):
    pass
""",
        "tests": [
            ("two_sum([2, 7, 11, 15], 9)", [0, 1]),
            ("two_sum([3, 2, 4], 6)", [1, 2]),
            ("two_sum([3, 3], 6)", [0, 1]),
            ("two_sum([1, 5, 3, 7], 8)", [1, 2]),
            ("two_sum([0, 4, 3, 0], 0)", [0, 3]),
        ],
    },
    {
        "id": 37,
        "name": "HE: FizzBuzz",
        "type": "humaneval",
        "description": (
            "1からnまでの文字列リストを返す関数を実装せよ。\n"
            "- 3の倍数: 'Fizz'\n"
            "- 5の倍数: 'Buzz'\n"
            "- 3と5の倍数: 'FizzBuzz'\n"
            "- それ以外: 数字の文字列\n\n"
            "例:\n"
            "  fizzbuzz(5) -> ['1', '2', 'Fizz', '4', 'Buzz']\n"
            "  fizzbuzz(15)[-1] -> 'FizzBuzz'\n"
            "  fizzbuzz(3) -> ['1', '2', 'Fizz']"
        ),
        "before": """\
def fizzbuzz(n):
    pass
""",
        "tests": [
            ("fizzbuzz(1)", ["1"]),
            ("fizzbuzz(3)", ["1", "2", "Fizz"]),
            ("fizzbuzz(5)", ["1", "2", "Fizz", "4", "Buzz"]),
            ("fizzbuzz(15)[-1]", "FizzBuzz"),
            ("len(fizzbuzz(100))", 100),
        ],
    },
    {
        "id": 38,
        "name": "HE: 回文判定",
        "type": "humaneval",
        "description": (
            "文字列が回文かどうかを判定する関数を実装せよ。\n"
            "大文字小文字を区別せず、英数字以外は無視すること。\n\n"
            "例:\n"
            "  is_palindrome('racecar') -> True\n"
            "  is_palindrome('A man a plan a canal Panama') -> True\n"
            "  is_palindrome('hello') -> False"
        ),
        "before": """\
def is_palindrome(s):
    pass
""",
        "tests": [
            ("is_palindrome('racecar')", True),
            ("is_palindrome('hello')", False),
            ("is_palindrome('A man a plan a canal Panama')", True),
            ("is_palindrome('')", True),
            ("is_palindrome('Was it a car or a cat I saw')", True),
        ],
    },
    {
        "id": 39,
        "name": "HE: フィボナッチ",
        "type": "humaneval",
        "description": (
            "n番目のフィボナッチ数を返す関数を実装せよ。\n"
            "fib(0)=0, fib(1)=1, fib(n)=fib(n-1)+fib(n-2)\n\n"
            "例:\n"
            "  fibonacci(0) -> 0\n"
            "  fibonacci(1) -> 1\n"
            "  fibonacci(10) -> 55"
        ),
        "before": """\
def fibonacci(n):
    pass
""",
        "tests": [
            ("fibonacci(0)", 0),
            ("fibonacci(1)", 1),
            ("fibonacci(5)", 5),
            ("fibonacci(10)", 55),
            ("fibonacci(20)", 6765),
        ],
    },
    {
        "id": 40,
        "name": "HE: リスト平坦化",
        "type": "humaneval",
        "description": (
            "ネストされたリストを1次元に平坦化する関数を実装せよ。\n"
            "任意の深さのネストに対応すること。\n\n"
            "例:\n"
            "  flatten([1, [2, 3], [4, [5, 6]]]) -> [1, 2, 3, 4, 5, 6]\n"
            "  flatten([[1, 2], [3]]) -> [1, 2, 3]\n"
            "  flatten([1, 2, 3]) -> [1, 2, 3]"
        ),
        "before": """\
def flatten(lst):
    pass
""",
        "tests": [
            ("flatten([1, [2, 3], [4, [5, 6]]])", [1, 2, 3, 4, 5, 6]),
            ("flatten([[1, 2], [3]])", [1, 2, 3]),
            ("flatten([1, 2, 3])", [1, 2, 3]),
            ("flatten([])", []),
            ("flatten([[[1]], [[2]], [[3]]])", [1, 2, 3]),
        ],
    },
    {
        "id": 41,
        "name": "HE: 母音カウント",
        "type": "humaneval",
        "description": (
            "文字列中の母音(a,e,i,o,u)の数を返す関数を実装せよ。\n"
            "大文字小文字を区別しないこと。\n\n"
            "例:\n"
            "  count_vowels('hello') -> 2\n"
            "  count_vowels('AEIOU') -> 5\n"
            "  count_vowels('xyz') -> 0"
        ),
        "before": """\
def count_vowels(s):
    pass
""",
        "tests": [
            ("count_vowels('hello')", 2),
            ("count_vowels('AEIOU')", 5),
            ("count_vowels('xyz')", 0),
            ("count_vowels('')", 0),
            ("count_vowels('Python Programming')", 4),
        ],
    },
    {
        "id": 42,
        "name": "HE: 重複除去（順序保持）",
        "type": "humaneval",
        "description": (
            "リストから重複を除去し、元の順序を保持した新しいリストを返す関数を実装せよ。\n\n"
            "例:\n"
            "  remove_duplicates([1, 2, 2, 3, 1]) -> [1, 2, 3]\n"
            "  remove_duplicates([4, 4, 4]) -> [4]\n"
            "  remove_duplicates([1, 2, 3]) -> [1, 2, 3]"
        ),
        "before": """\
def remove_duplicates(lst):
    pass
""",
        "tests": [
            ("remove_duplicates([1, 2, 2, 3, 1])", [1, 2, 3]),
            ("remove_duplicates([4, 4, 4])", [4]),
            ("remove_duplicates([1, 2, 3])", [1, 2, 3]),
            ("remove_duplicates([])", []),
            ("remove_duplicates(['a', 'b', 'a', 'c'])", ["a", "b", "c"]),
        ],
    },
    {
        "id": 43,
        "name": "HE: 最大公約数",
        "type": "humaneval",
        "description": (
            "2つの正の整数の最大公約数(GCD)を返す関数を実装せよ。\n"
            "math.gcdを使わず、ユークリッドの互除法で実装すること。\n\n"
            "例:\n"
            "  gcd(12, 8) -> 4\n"
            "  gcd(7, 13) -> 1\n"
            "  gcd(100, 75) -> 25"
        ),
        "before": """\
def gcd(a, b):
    pass
""",
        "tests": [
            ("gcd(12, 8)", 4),
            ("gcd(7, 13)", 1),
            ("gcd(100, 75)", 25),
            ("gcd(1, 1)", 1),
            ("gcd(48, 18)", 6),
        ],
    },
    # ── HumanEval-Pure（純粋な問題文のみ、例示なし）──
    {
        "id": 44,
        "name": "HE-Pure: 括弧の整合性チェック",
        "type": "humaneval",
        "description": "文字列中の括弧 (), [], {} が正しく対応しているかを判定する関数を実装せよ。",
        "before": """\
def is_valid_brackets(s):
    pass
""",
        "tests": [
            ("is_valid_brackets('()')", True),
            ("is_valid_brackets('()[]{}')", True),
            ("is_valid_brackets('(]')", False),
            ("is_valid_brackets('([)]')", False),
            ("is_valid_brackets('{[]}')", True),
            ("is_valid_brackets('')", True),
        ],
    },
    {
        "id": 45,
        "name": "HE-Pure: ローマ数字→整数変換",
        "type": "humaneval",
        "description": "ローマ数字の文字列を整数に変換する関数を実装せよ。入力は1〜3999の範囲。",
        "before": """\
def roman_to_int(s):
    pass
""",
        "tests": [
            ("roman_to_int('III')", 3),
            ("roman_to_int('IV')", 4),
            ("roman_to_int('IX')", 9),
            ("roman_to_int('XLII')", 42),
            ("roman_to_int('MCMXCIV')", 1994),
            ("roman_to_int('MMXXVI')", 2026),
        ],
    },
    {
        "id": 46,
        "name": "HE-Pure: 最大部分配列和",
        "type": "humaneval",
        "description": "整数リストの連続する部分配列の最大和を返す関数を実装せよ。リストは1要素以上。",
        "before": """\
def max_subarray_sum(nums):
    pass
""",
        "tests": [
            ("max_subarray_sum([-2,1,-3,4,-1,2,1,-5,4])", 6),
            ("max_subarray_sum([1])", 1),
            ("max_subarray_sum([5,4,-1,7,8])", 23),
            ("max_subarray_sum([-1,-2,-3])", -1),
            ("max_subarray_sum([1,2,3,4,5])", 15),
        ],
    },
    {
        "id": 47,
        "name": "HE-Pure: ソート済みリストのマージ",
        "type": "humaneval",
        "description": "2つのソート済みリストを1つのソート済みリストにマージする関数を実装せよ。",
        "before": """\
def merge_sorted(list1, list2):
    pass
""",
        "tests": [
            ("merge_sorted([1,3,5], [2,4,6])", [1,2,3,4,5,6]),
            ("merge_sorted([], [1,2,3])", [1,2,3]),
            ("merge_sorted([1,2,3], [])", [1,2,3]),
            ("merge_sorted([1,1], [1,1])", [1,1,1,1]),
            ("merge_sorted([-3,0,5], [-2,1,4])", [-3,-2,0,1,4,5]),
        ],
    },
    {
        "id": 48,
        "name": "HE-Pure: 行列の転置",
        "type": "humaneval",
        "description": "2次元リスト（行列）を転置する関数を実装せよ。",
        "before": """\
def transpose(matrix):
    pass
""",
        "tests": [
            ("transpose([[1,2,3],[4,5,6]])", [[1,4],[2,5],[3,6]]),
            ("transpose([[1]])", [[1]]),
            ("transpose([[1,2],[3,4],[5,6]])", [[1,3,5],[2,4,6]]),
            ("transpose([[1,2,3]])", [[1],[2],[3]]),
        ],
    },
    {
        "id": 49,
        "name": "HE-Pure: 文字列圧縮",
        "type": "humaneval",
        "description": "連続する同一文字を文字+出現回数に圧縮する関数を実装せよ。1回の場合も数字を付ける。",
        "before": """\
def compress(s):
    pass
""",
        "tests": [
            ("compress('aabcccccaaa')", "a2b1c5a3"),
            ("compress('abc')", "a1b1c1"),
            ("compress('aaa')", "a3"),
            ("compress('')", ""),
            ("compress('a')", "a1"),
        ],
    },
    {
        "id": 50,
        "name": "HE-Pure: 素数判定",
        "type": "humaneval",
        "description": "与えられた整数が素数かどうかを判定する関数を実装せよ。",
        "before": """\
def is_prime(n):
    pass
""",
        "tests": [
            ("is_prime(2)", True),
            ("is_prime(1)", False),
            ("is_prime(17)", True),
            ("is_prime(4)", False),
            ("is_prime(97)", True),
            ("is_prime(100)", False),
        ],
    },
    {
        "id": 51,
        "name": "HE-Pure: 単語出現頻度",
        "type": "humaneval",
        "description": "文字列中の各単語の出現回数を辞書で返す関数を実装せよ。大文字小文字を区別しない。",
        "before": """\
def word_count(text):
    pass
""",
        "tests": [
            ("word_count('hello world hello')", {"hello": 2, "world": 1}),
            ("word_count('a A a')", {"a": 3}),
            ("word_count('')", {}),
            ("word_count('one')", {"one": 1}),
            ("word_count('The the THE')", {"the": 3}),
        ],
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


def _score_humaneval(task: dict, after_code: str) -> float:
    """HumanEval系: テストケース通過率でスコアリング"""
    tests = task.get("tests", [])
    if not tests:
        return 0.0

    # コードをパース・構文チェック
    try:
        ast.parse(after_code)
    except SyntaxError:
        return 0.0

    # コードを実行して関数を取得
    namespace = {}
    try:
        exec(after_code, namespace)
    except Exception:
        return 0.1  # 構文OKだが実行エラー

    # テストケース通過率を計算
    passed = 0
    for test_expr, expected in tests:
        try:
            result = eval(test_expr, namespace)
            if result == expected:
                passed += 1
        except Exception:
            pass

    # スコア = 0.2(構文OK) + 0.8 * (通過率)
    ratio = passed / len(tests)
    return round(0.2 + 0.8 * ratio, 2)


def _score_task26_scenario_template(after_code: str) -> float:
    """タスク26: シナリオテンプレート生成 — 辞書構造・キーワード・docstring"""
    score = 0.0
    try:
        tree = ast.parse(after_code)
    except SyntaxError:
        return 0.0
    score += 0.2

    # 1. 辞書を返す構造（Dict/return）(0.25)
    has_dict = any(isinstance(node, ast.Dict) for node in ast.walk(tree))
    has_return = any(isinstance(node, ast.Return) for node in ast.walk(tree))
    if has_dict and has_return:
        score += 0.25
    elif has_return:
        score += 0.1

    # 2. scene/characters/dialogueキーワードが含まれる (0.2)
    code_lower = after_code.lower()
    keywords = ["scene", "character", "dialogue"]
    found = sum(1 for kw in keywords if kw in code_lower)
    if found >= 3:
        score += 0.2
    elif found >= 2:
        score += 0.1

    # 3. 関数が維持されている (0.1)
    has_func = any(isinstance(node, ast.FunctionDef) for node in ast.walk(tree))
    if has_func:
        score += 0.1

    # 4. docstringが存在する (0.25)
    has_docstring = any(
        isinstance(node, ast.FunctionDef) and ast.get_docstring(node)
        for node in ast.walk(tree)
    )
    if has_docstring:
        score += 0.25

    return round(min(score, 1.0), 2)


def _score_task27_character_parser(after_code: str) -> float:
    """タスク27: キャラクター設定パーサー — 辞書返却・バリデーション・docstring"""
    score = 0.0
    try:
        tree = ast.parse(after_code)
    except SyntaxError:
        return 0.0
    score += 0.2

    # 1. 辞書を返す構造 (0.2)
    has_dict = any(isinstance(node, ast.Dict) for node in ast.walk(tree))
    if has_dict:
        score += 0.2

    # 2. name/role/traitキーワード (0.15)
    code_lower = after_code.lower()
    keywords = ["name", "role", "trait"]
    found = sum(1 for kw in keywords if kw in code_lower)
    if found >= 3:
        score += 0.15
    elif found >= 2:
        score += 0.1

    # 3. エラーハンドリング（try/except or raise ValueError）(0.2)
    has_try = any(isinstance(node, ast.Try) for node in ast.walk(tree))
    has_raise = any(isinstance(node, ast.Raise) for node in ast.walk(tree))
    if has_try or has_raise:
        score += 0.2

    # 4. docstringが存在する (0.25)
    has_docstring = any(
        isinstance(node, ast.FunctionDef) and ast.get_docstring(node)
        for node in ast.walk(tree)
    )
    if has_docstring:
        score += 0.25

    return round(min(score, 1.0), 2)


def _score_task28_dialogue_formatter(after_code: str) -> float:
    """タスク28: セリフフォーマッター — リスト対応・バリデーション・docstring"""
    score = 0.0
    try:
        tree = ast.parse(after_code)
    except SyntaxError:
        return 0.0
    score += 0.2

    # 1. 関数が維持されreturnがある (0.15)
    has_func = any(isinstance(node, ast.FunctionDef) for node in ast.walk(tree))
    has_return = any(isinstance(node, ast.Return) for node in ast.walk(tree))
    if has_func and has_return:
        score += 0.15

    # 2. 入力チェック（if文 or isinstance or raise）(0.2)
    has_guard = any(isinstance(node, ast.If) for node in ast.walk(tree))
    has_isinstance = "isinstance" in after_code
    has_raise = any(isinstance(node, ast.Raise) for node in ast.walk(tree))
    if has_guard or has_isinstance or has_raise:
        score += 0.2

    # 3. リスト対応（forループ or isinstance(line, list)）(0.2)
    has_for = any(isinstance(node, ast.For) for node in ast.walk(tree))
    has_list_check = "list" in after_code
    if has_for or has_list_check:
        score += 0.2

    # 4. docstringが存在する (0.25)
    has_docstring = any(
        isinstance(node, ast.FunctionDef) and ast.get_docstring(node)
        for node in ast.walk(tree)
    )
    if has_docstring:
        score += 0.25

    return round(min(score, 1.0), 2)


def _score_task29_csv_parser(after_code: str) -> float:
    """タスク29: CSV→辞書変換 — csvモジュール or ヘッダー処理・辞書返却・docstring"""
    score = 0.0
    try:
        tree = ast.parse(after_code)
    except SyntaxError:
        return 0.0
    score += 0.2

    # 1. csvモジュール使用 or ヘッダー処理 (0.25)
    has_csv_import = "import csv" in after_code or "from csv" in after_code
    has_header = "header" in after_code.lower() or "[0]" in after_code
    if has_csv_import:
        score += 0.25
    elif has_header:
        score += 0.15

    # 2. 辞書を構築している（dict/Dict/{}）(0.2)
    has_dict = any(isinstance(node, (ast.Dict, ast.DictComp)) for node in ast.walk(tree))
    has_dict_call = any(
        isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "dict"
        for node in ast.walk(tree)
    )
    if has_dict or has_dict_call or "zip" in after_code:
        score += 0.2

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


def _score_task30_date_format(after_code: str) -> float:
    """タスク30: 日付フォーマット統一 — datetime使用・strftime・docstring"""
    score = 0.0
    try:
        tree = ast.parse(after_code)
    except SyntaxError:
        return 0.0
    score += 0.2

    # 1. datetimeモジュールを使用 (0.3)
    has_datetime = "datetime" in after_code
    if has_datetime:
        score += 0.3

    # 2. strftime or strptime or date()呼び出し (0.2)
    has_strftime = "strftime" in after_code or "strptime" in after_code
    has_date_call = "date(" in after_code or "datetime(" in after_code
    if has_strftime or has_date_call:
        score += 0.2

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


def _score_task31_retry_decorator(after_code: str) -> float:
    """タスク31: リトライデコレータ — デコレータパターン・ネスト関数・引数・docstring"""
    score = 0.0
    try:
        tree = ast.parse(after_code)
    except SyntaxError:
        return 0.0
    score += 0.2

    # 1. デコレータ付き関数がある (0.25)
    has_decorator = any(
        isinstance(node, ast.FunctionDef) and node.decorator_list
        for node in ast.walk(tree)
    )
    if has_decorator:
        score += 0.25

    # 2. wrapper/inner関数パターン (0.2)
    has_nested = False
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            inner_funcs = [n for n in ast.walk(node) if isinstance(n, ast.FunctionDef) and n is not node]
            if inner_funcs:
                has_nested = True
                break
    if has_nested:
        score += 0.2

    # 3. try/exceptでリトライロジック (0.15)
    has_try = any(isinstance(node, ast.Try) for node in ast.walk(tree))
    has_for = any(isinstance(node, ast.For) for node in ast.walk(tree))
    if has_try and has_for:
        score += 0.15
    elif has_try:
        score += 0.1

    # 4. docstringが存在する (0.2)
    has_docstring = any(
        isinstance(node, ast.FunctionDef) and ast.get_docstring(node)
        for node in ast.walk(tree)
    )
    if has_docstring:
        score += 0.2

    return round(min(score, 1.0), 2)


def _score_task32_validation(after_code: str) -> float:
    """タスク32: バリデーション関数 — isinstance・raise・メッセージ・docstring"""
    score = 0.0
    try:
        tree = ast.parse(after_code)
    except SyntaxError:
        return 0.0
    score += 0.2

    # 1. isinstanceまたは型チェック (0.2)
    has_isinstance = "isinstance" in after_code
    has_type_check = any(isinstance(node, ast.If) for node in ast.walk(tree))
    if has_isinstance:
        score += 0.2
    elif has_type_check:
        score += 0.1

    # 2. raise ValueError/TypeError (0.2)
    specific = {"ValueError", "TypeError"}
    has_raise = False
    for node in ast.walk(tree):
        if isinstance(node, ast.Raise) and node.exc:
            if isinstance(node.exc, ast.Call) and isinstance(node.exc.func, ast.Name):
                if node.exc.func.id in specific:
                    has_raise = True
    if has_raise:
        score += 0.2

    # 3. エラーメッセージが具体的（引数付きraise）(0.15)
    has_msg = False
    for node in ast.walk(tree):
        if isinstance(node, ast.Raise) and node.exc and isinstance(node.exc, ast.Call):
            if node.exc.args:
                has_msg = True
    if has_msg:
        score += 0.15

    # 4. docstringが存在する (0.25)
    has_docstring = any(
        isinstance(node, ast.FunctionDef) and ast.get_docstring(node)
        for node in ast.walk(tree)
    )
    if has_docstring:
        score += 0.25

    return round(min(score, 1.0), 2)


def _score_task33_friendly_errors(after_code: str) -> float:
    """タスク33: エラーメッセージ改善 — 親切なメッセージ・提案含む・docstring"""
    score = 0.0
    try:
        tree = ast.parse(after_code)
    except SyntaxError:
        return 0.0
    score += 0.2

    # 1. raise文が維持されている (0.15)
    raises = [n for n in ast.walk(tree) if isinstance(n, ast.Raise)]
    if raises:
        score += 0.15

    # 2. エラーメッセージが長くなっている（具体的・親切）(0.25)
    msg_lengths = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Raise) and node.exc and isinstance(node.exc, ast.Call):
            for arg in node.exc.args:
                if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                    msg_lengths.append(len(arg.value))
                elif isinstance(arg, ast.JoinedStr):
                    msg_lengths.append(30)  # f-stringは十分長いとみなす
    if msg_lengths and all(m > 15 for m in msg_lengths):
        score += 0.25
    elif msg_lengths and any(m > 15 for m in msg_lengths):
        score += 0.15

    # 3. "Error: invalid"のような冷たいメッセージが除去されている (0.15)
    cold_msgs = ["error: invalid", "error: wrong type", "error: too long"]
    has_cold = any(cm in after_code.lower() for cm in cold_msgs)
    if not has_cold:
        score += 0.15

    # 4. docstringが存在する (0.25)
    has_docstring = any(
        isinstance(node, ast.FunctionDef) and ast.get_docstring(node)
        for node in ast.walk(tree)
    )
    if has_docstring:
        score += 0.25

    return round(min(score, 1.0), 2)


def _score_task34_greeting(after_code: str) -> float:
    """タスク34: 挨拶文生成 — 時間帯判定・名前パラメータ・docstring"""
    score = 0.0
    try:
        tree = ast.parse(after_code)
    except SyntaxError:
        return 0.0
    score += 0.2

    # 1. datetime/time使用 (0.2)
    has_datetime = "datetime" in after_code or "import time" in after_code
    if has_datetime:
        score += 0.2

    # 2. 時間帯に応じた条件分岐（if文が複数）(0.2)
    ifs = [n for n in ast.walk(tree) if isinstance(n, ast.If)]
    if len(ifs) >= 2:
        score += 0.2
    elif len(ifs) >= 1:
        score += 0.1

    # 3. 名前引数がある（引数2つ以上 or name引数）(0.15)
    funcs = [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]
    has_name_arg = False
    for func in funcs:
        if len(func.args.args) >= 1:
            for arg in func.args.args:
                if arg.arg in ("name", "user_name", "username"):
                    has_name_arg = True
            if len(func.args.args) >= 1 and func.args.defaults:
                has_name_arg = True
    if has_name_arg:
        score += 0.15

    # 4. docstringが存在する (0.25)
    has_docstring = any(
        isinstance(node, ast.FunctionDef) and ast.get_docstring(node)
        for node in ast.walk(tree)
    )
    if has_docstring:
        score += 0.25

    return round(min(score, 1.0), 2)


def _score_task35_help_text(after_code: str) -> float:
    """タスク35: ヘルプテキスト改善 — return化・セクション分け・使用例・docstring"""
    score = 0.0
    try:
        tree = ast.parse(after_code)
    except SyntaxError:
        return 0.0
    score += 0.2

    # 1. printではなくreturnで返している (0.2)
    has_return = any(isinstance(node, ast.Return) for node in ast.walk(tree))
    print_calls = [
        n for n in ast.walk(tree)
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Name)
        and n.func.id == "print"
    ]
    if has_return and not print_calls:
        score += 0.2
    elif has_return:
        score += 0.1

    # 2. 使用例キーワード（usage/example）(0.2)
    code_lower = after_code.lower()
    has_usage = "usage" in code_lower or "example" in code_lower
    if has_usage:
        score += 0.2

    # 3. セクション分け（複数の文字列 or \n\n）(0.15)
    has_sections = after_code.count("\\n") >= 3 or after_code.count("\n\n") >= 2
    if has_sections:
        score += 0.15

    # 4. docstringが存在する (0.25)
    has_docstring = any(
        isinstance(node, ast.FunctionDef) and ast.get_docstring(node)
        for node in ast.walk(tree)
    )
    if has_docstring:
        score += 0.25

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
        26: lambda code: _score_task26_scenario_template(code),
        27: lambda code: _score_task27_character_parser(code),
        28: lambda code: _score_task28_dialogue_formatter(code),
        29: lambda code: _score_task29_csv_parser(code),
        30: lambda code: _score_task30_date_format(code),
        31: lambda code: _score_task31_retry_decorator(code),
        32: lambda code: _score_task32_validation(code),
        33: lambda code: _score_task33_friendly_errors(code),
        34: lambda code: _score_task34_greeting(code),
        35: lambda code: _score_task35_help_text(code),
        36: lambda code: _score_humaneval(task, code),
        37: lambda code: _score_humaneval(task, code),
        38: lambda code: _score_humaneval(task, code),
        39: lambda code: _score_humaneval(task, code),
        40: lambda code: _score_humaneval(task, code),
        41: lambda code: _score_humaneval(task, code),
        42: lambda code: _score_humaneval(task, code),
        43: lambda code: _score_humaneval(task, code),
        44: lambda code: _score_humaneval(task, code),
        45: lambda code: _score_humaneval(task, code),
        46: lambda code: _score_humaneval(task, code),
        47: lambda code: _score_humaneval(task, code),
        48: lambda code: _score_humaneval(task, code),
        49: lambda code: _score_humaneval(task, code),
        50: lambda code: _score_humaneval(task, code),
        51: lambda code: _score_humaneval(task, code),
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
