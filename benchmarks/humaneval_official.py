"""HumanEval公式50問ベンチマーク（純粋実力測定用）

HumanEval 164問からeasy〜medium難易度の50問を選定。
task_pool.jsonには連携しない測定専用ベンチマーク。

評価方法: unittest通過率（pass@1）
"""

from __future__ import annotations

import ast
import traceback

# ─────────────────────────────────────────
# 50問定義（HumanEval公式問題番号付き）
# ─────────────────────────────────────────

HUMANEVAL_TASKS = [
    # HumanEval/0
    {
        "he_id": 0,
        "name": "has_close_elements",
        "description": (
            "Check if in given list of numbers, are any two numbers closer to each other "
            "than given threshold.\n"
            ">>> has_close_elements([1.0, 2.0, 3.0], 0.5)\n"
            "False\n"
            ">>> has_close_elements([1.0, 2.8, 3.0, 4.0, 5.0, 2.0], 0.3)\n"
            "True"
        ),
        "before": "from typing import List\n\ndef has_close_elements(numbers: List[float], threshold: float) -> bool:\n    pass",
        "tests": [
            ("has_close_elements([1.0, 2.0, 3.9, 4.0, 5.0, 2.2], 0.3)", True),
            ("has_close_elements([1.0, 2.0, 3.9, 4.0, 5.0, 2.2], 0.05)", False),
            ("has_close_elements([1.0, 2.0, 5.9, 4.0, 5.0], 0.95)", True),
            ("has_close_elements([1.0, 2.0, 5.9, 4.0, 5.0], 0.8)", False),
            ("has_close_elements([1.0, 2.0, 3.0, 4.0, 5.0, 2.0], 0.1)", True),
        ],
    },
    # HumanEval/1
    {
        "he_id": 1,
        "name": "separate_paren_groups",
        "description": (
            "Input to this function is a string containing multiple groups of nested parentheses. "
            "Your goal is to separate those group into separate strings and return the list of those.\n"
            "Separate groups are balanced (each open brace is properly closed) and not nested within each other.\n"
            "Ignore any spaces in the input string.\n"
            ">>> separate_paren_groups('( ) (( )) (( )( ))')\n"
            "['()', '(())', '(()())']"
        ),
        "before": "from typing import List\n\ndef separate_paren_groups(paren_string: str) -> List[str]:\n    pass",
        "tests": [
            ("separate_paren_groups('(()()) ((())) () ((())()())')", ['(()())', '((()))', '()', '((())()())']),
            ("separate_paren_groups('() (()) ((())) (((())))')", ['()', '(())', '((()))', '(((())))']),
            ("separate_paren_groups('(()(())((())))')", ['(()(())((())))']),
            ("separate_paren_groups('( ) (( )) (( )( ))')", ['()', '(())', '(()())']),
        ],
    },
    # HumanEval/2
    {
        "he_id": 2,
        "name": "truncate_number",
        "description": (
            "Given a positive floating point number, it can be decomposed into an integer part "
            "(largest integer smaller than given number) and decimals (leftover part always smaller than 1).\n"
            "Return the decimal part of the number.\n"
            ">>> truncate_number(3.5)\n"
            "0.5"
        ),
        "before": "def truncate_number(number: float) -> float:\n    pass",
        "tests": [
            ("truncate_number(3.5)", 0.5),
            ("abs(truncate_number(1.33) - 0.33) < 1e-6", True),
            ("abs(truncate_number(123.456) - 0.456) < 1e-6", True),
        ],
    },
    # HumanEval/4
    {
        "he_id": 4,
        "name": "mean_absolute_deviation",
        "description": (
            "For a given list of input numbers, calculate Mean Absolute Deviation around the mean of this dataset.\n"
            "Mean Absolute Deviation is the average absolute difference between each element and a centerpoint (mean in this case):\n"
            "MAD = average | x - x_mean |\n"
            ">>> mean_absolute_deviation([1.0, 2.0, 3.0, 4.0])\n"
            "1.0"
        ),
        "before": "from typing import List\n\ndef mean_absolute_deviation(numbers: List[float]) -> float:\n    pass",
        "tests": [
            ("abs(mean_absolute_deviation([1.0, 2.0, 3.0, 4.0]) - 1.0) < 1e-6", True),
            ("abs(mean_absolute_deviation([1.0, 2.0, 3.0]) - 2.0/3.0) < 1e-6", True),
            ("abs(mean_absolute_deviation([1.0, 1.0, 1.0, 1.0]) - 0.0) < 1e-6", True),
        ],
    },
    # HumanEval/5
    {
        "he_id": 5,
        "name": "intersperse",
        "description": (
            "Insert a number 'delimiter' between every two consecutive elements of input list `numbers`.\n"
            ">>> intersperse([], 4)\n"
            "[]\n"
            ">>> intersperse([1, 2, 3], 4)\n"
            "[1, 4, 2, 4, 3]"
        ),
        "before": "from typing import List\n\ndef intersperse(numbers: List[int], delimiter: int) -> List[int]:\n    pass",
        "tests": [
            ("intersperse([], 7)", []),
            ("intersperse([5, 6, 3, 2], 8)", [5, 8, 6, 8, 3, 8, 2]),
            ("intersperse([2, 2, 2], 2)", [2, 2, 2, 2, 2]),
        ],
    },
    # HumanEval/6
    {
        "he_id": 6,
        "name": "parse_nested_parens",
        "description": (
            "Input to this function is a string represented multiple groups of nested parentheses separated by spaces.\n"
            "For each of the group, output the deepest level of nesting of parentheses.\n"
            ">>> parse_nested_parens('(()()) ((())) () ((())()())')\n"
            "[2, 3, 1, 3]"
        ),
        "before": "from typing import List\n\ndef parse_nested_parens(paren_string: str) -> List[int]:\n    pass",
        "tests": [
            ("parse_nested_parens('(()()) ((())) () ((())()())')", [2, 3, 1, 3]),
            ("parse_nested_parens('() (()) ((())) (((())))')", [1, 2, 3, 4]),
            ("parse_nested_parens('(()(())((())))')", [4]),
        ],
    },
    # HumanEval/7
    {
        "he_id": 7,
        "name": "filter_by_substring",
        "description": (
            "Filter an input list of strings only for ones that contain given substring.\n"
            ">>> filter_by_substring([], 'a')\n"
            "[]\n"
            ">>> filter_by_substring(['abc', 'bacd', 'cde', 'array'], 'a')\n"
            "['abc', 'bacd', 'array']"
        ),
        "before": "from typing import List\n\ndef filter_by_substring(strings: List[str], substring: str) -> List[str]:\n    pass",
        "tests": [
            ("filter_by_substring([], 'john')", []),
            ("filter_by_substring(['xxx', 'asd', 'xxy', 'john doe', 'xxxuj', 'xxx hijk'], 'xxx')", ['xxx', 'xxxuj', 'xxx hijk']),
            ("filter_by_substring(['xxx', 'asd', 'aaber', 'john doe', 'xxxuj', 'xxx hijk'], 'xx')", ['xxx', 'xxxuj', 'xxx hijk']),
            ("filter_by_substring(['grunt', 'hierarchies', 'his', 'hierarchical'], 'hi')", ['hierarchies', 'his', 'hierarchical']),
        ],
    },
    # HumanEval/8
    {
        "he_id": 8,
        "name": "sum_product",
        "description": (
            "For a given list of integers, return a tuple consisting of a sum and a product of all the integers in a list.\n"
            "Empty sum should be equal to 0 and empty product should be equal to 1.\n"
            ">>> sum_product([])\n"
            "(0, 1)\n"
            ">>> sum_product([1, 2, 3, 4])\n"
            "(10, 24)"
        ),
        "before": "from typing import List, Tuple\n\ndef sum_product(numbers: List[int]) -> Tuple[int, int]:\n    pass",
        "tests": [
            ("sum_product([])", (0, 1)),
            ("sum_product([1, 1, 1])", (3, 1)),
            ("sum_product([100, 0])", (100, 0)),
            ("sum_product([3, 5, 7])", (15, 105)),
            ("sum_product([10])", (10, 10)),
        ],
    },
    # HumanEval/9
    {
        "he_id": 9,
        "name": "rolling_max",
        "description": (
            "From a given list of integers, generate a list of rolling maximum element found until given moment in the sequence.\n"
            ">>> rolling_max([1, 2, 3, 2, 3, 4, 2])\n"
            "[1, 2, 3, 3, 3, 4, 4]"
        ),
        "before": "from typing import List\n\ndef rolling_max(numbers: List[int]) -> List[int]:\n    pass",
        "tests": [
            ("rolling_max([])", []),
            ("rolling_max([1, 2, 3, 2, 3, 4, 2])", [1, 2, 3, 3, 3, 4, 4]),
            ("rolling_max([1, 4, 2, 3, 5])", [1, 4, 4, 4, 5]),
            ("rolling_max([5, 4, 3, 2, 1])", [5, 5, 5, 5, 5]),
        ],
    },
    # HumanEval/11
    {
        "he_id": 11,
        "name": "string_xor",
        "description": (
            "Input are two strings a and b consisting only of 1s and 0s.\n"
            "Perform binary XOR on these inputs and return result also as a string.\n"
            ">>> string_xor('010', '110')\n"
            "'100'"
        ),
        "before": "def string_xor(a: str, b: str) -> str:\n    pass",
        "tests": [
            ("string_xor('111000', '101010')", '010010'),
            ("string_xor('1', '1')", '0'),
            ("string_xor('0101', '0000')", '0101'),
        ],
    },
    # HumanEval/12
    {
        "he_id": 12,
        "name": "longest",
        "description": (
            "Out of list of strings, return the longest one. "
            "Return the first one in case of multiple strings of the same length. "
            "Return None in case the input list is empty.\n"
            ">>> longest([])\n"
            ">>> longest(['a', 'b', 'c'])\n"
            "'a'\n"
            ">>> longest(['a', 'bb', 'ccc'])\n"
            "'ccc'"
        ),
        "before": "from typing import List, Optional\n\ndef longest(strings: List[str]) -> Optional[str]:\n    pass",
        "tests": [
            ("longest([])", None),
            ("longest(['x', 'y', 'z'])", 'x'),
            ("longest(['x', 'yyy', 'zzzz', 'www', 'kkkk', 'abc'])", 'zzzz'),
        ],
    },
    # HumanEval/13
    {
        "he_id": 13,
        "name": "greatest_common_divisor",
        "description": (
            "Return a greatest common divisor of two integers a and b.\n"
            ">>> greatest_common_divisor(3, 5)\n"
            "1\n"
            ">>> greatest_common_divisor(25, 15)\n"
            "5"
        ),
        "before": "def greatest_common_divisor(a: int, b: int) -> int:\n    pass",
        "tests": [
            ("greatest_common_divisor(3, 7)", 1),
            ("greatest_common_divisor(10, 15)", 5),
            ("greatest_common_divisor(49, 14)", 7),
            ("greatest_common_divisor(144, 60)", 12),
        ],
    },
    # HumanEval/14
    {
        "he_id": 14,
        "name": "all_prefixes",
        "description": (
            "Return list of all prefixes from shortest to longest of the input string.\n"
            ">>> all_prefixes('abc')\n"
            "['a', 'ab', 'abc']"
        ),
        "before": "from typing import List\n\ndef all_prefixes(string: str) -> List[str]:\n    pass",
        "tests": [
            ("all_prefixes('')", []),
            ("all_prefixes('asdfgh')", ['a', 'as', 'asd', 'asdf', 'asdfg', 'asdfgh']),
            ("all_prefixes('WWW')", ['W', 'WW', 'WWW']),
        ],
    },
    # HumanEval/15
    {
        "he_id": 15,
        "name": "string_sequence",
        "description": (
            "Return a string containing space-delimited numbers starting from 0 up to n inclusive.\n"
            ">>> string_sequence(0)\n"
            "'0'\n"
            ">>> string_sequence(5)\n"
            "'0 1 2 3 4 5'"
        ),
        "before": "def string_sequence(n: int) -> str:\n    pass",
        "tests": [
            ("string_sequence(0)", '0'),
            ("string_sequence(3)", '0 1 2 3'),
            ("string_sequence(10)", '0 1 2 3 4 5 6 7 8 9 10'),
        ],
    },
    # HumanEval/16
    {
        "he_id": 16,
        "name": "count_distinct_characters",
        "description": (
            "Given a string, find out how many distinct characters (regardless of case) does it consist of.\n"
            ">>> count_distinct_characters('xyzXYZ')\n"
            "3\n"
            ">>> count_distinct_characters('Jerry')\n"
            "4"
        ),
        "before": "def count_distinct_characters(string: str) -> int:\n    pass",
        "tests": [
            ("count_distinct_characters('')", 0),
            ("count_distinct_characters('abcde')", 5),
            ("count_distinct_characters('abcdecadeCADE')", 5),
            ("count_distinct_characters('aaaaAAAAaaaa')", 1),
            ("count_distinct_characters('Jerry jERRY JeRRy')", 5),
        ],
    },
    # HumanEval/17
    {
        "he_id": 17,
        "name": "parse_music",
        "description": (
            "Input to this function is a string representing musical notes in a special ASCII format.\n"
            "Your task is to parse this string and return list of integers corresponding to how many beats does each note last.\n"
            "Here is a legend:\n"
            "'o' - whole note, lasts four beats\n"
            "'o|' - half note, lasts two beats\n"
            "'.|' - quarter note, lasts one beat\n"
            ">>> parse_music('o o| .| o| o| .| .| .| .| o o')\n"
            "[4, 2, 1, 2, 2, 1, 1, 1, 1, 4, 4]"
        ),
        "before": "from typing import List\n\ndef parse_music(music_string: str) -> List[int]:\n    pass",
        "tests": [
            ("parse_music('')", []),
            ("parse_music('o o o o')", [4, 4, 4, 4]),
            ("parse_music('.| .| .| .|')", [1, 1, 1, 1]),
            ("parse_music('o| o| .| .| o o o o')", [2, 2, 1, 1, 4, 4, 4, 4]),
            ("parse_music('o| .| o| .| o o| o o|')", [2, 1, 2, 1, 4, 2, 4, 2]),
        ],
    },
    # HumanEval/18
    {
        "he_id": 18,
        "name": "how_many_times",
        "description": (
            "Find how many times a given substring can be found in the original string. Count overlapping cases.\n"
            ">>> how_many_times('', 'a')\n"
            "0\n"
            ">>> how_many_times('aaa', 'a')\n"
            "3\n"
            ">>> how_many_times('aaaa', 'aa')\n"
            "3"
        ),
        "before": "def how_many_times(string: str, substring: str) -> int:\n    pass",
        "tests": [
            ("how_many_times('', 'x')", 0),
            ("how_many_times('xyxyxyx', 'x')", 4),
            ("how_many_times('cacacacac', 'cac')", 4),
            ("how_many_times('john doe', 'john')", 1),
        ],
    },
    # HumanEval/20
    {
        "he_id": 20,
        "name": "find_closest_elements",
        "description": (
            "From a supplied list of numbers (of length at least two) select and return two that are the closest to each other "
            "and return them in order (smaller number, larger number).\n"
            ">>> find_closest_elements([1.0, 2.0, 3.0, 4.0, 5.0, 2.2])\n"
            "(2.0, 2.2)"
        ),
        "before": "from typing import List, Tuple\n\ndef find_closest_elements(numbers: List[float]) -> Tuple[float, float]:\n    pass",
        "tests": [
            ("find_closest_elements([1.0, 2.0, 3.0, 4.0, 5.0, 2.2])", (2.0, 2.2)),
            ("find_closest_elements([1.0, 2.0, 3.0, 4.0, 5.0, 2.0])", (2.0, 2.0)),
            ("find_closest_elements([1.1, 2.2, 3.1, 4.1, 5.1])", (2.2, 3.1)),
        ],
    },
    # HumanEval/21
    {
        "he_id": 21,
        "name": "rescale_to_unit",
        "description": (
            "Given list of numbers (of at least two elements), apply a linear transform to that list, "
            "such that the smallest number will become 0 and the largest will become 1.\n"
            ">>> rescale_to_unit([1.0, 2.0, 3.0, 4.0, 5.0])\n"
            "[0.0, 0.25, 0.5, 0.75, 1.0]"
        ),
        "before": "from typing import List\n\ndef rescale_to_unit(numbers: List[float]) -> List[float]:\n    pass",
        "tests": [
            ("rescale_to_unit([2.0, 49.9])", [0.0, 1.0]),
            ("rescale_to_unit([100.0, 49.9])", [1.0, 0.0]),
            ("[round(x, 4) for x in rescale_to_unit([1.0, 2.0, 3.0, 4.0, 5.0])]", [0.0, 0.25, 0.5, 0.75, 1.0]),
        ],
    },
    # HumanEval/22
    {
        "he_id": 22,
        "name": "filter_integers",
        "description": (
            "Filter given list of any python values only for integers.\n"
            ">>> filter_integers(['a', 3.14, 5])\n"
            "[5]\n"
            ">>> filter_integers([1, 2, 3, 'abc', {}, []])\n"
            "[1, 2, 3]"
        ),
        "before": "from typing import Any, List\n\ndef filter_integers(values: List[Any]) -> List[int]:\n    pass",
        "tests": [
            ("filter_integers([])", []),
            ("filter_integers([4, {}, [], 23.2, 9, 'adasd'])", [4, 9]),
            ("filter_integers([3, 'c', 3, 3, 'a', 'b'])", [3, 3, 3]),
        ],
    },
    # HumanEval/23
    {
        "he_id": 23,
        "name": "strlen",
        "description": (
            "Return length of given string.\n"
            ">>> strlen('')\n"
            "0\n"
            ">>> strlen('abc')\n"
            "3"
        ),
        "before": "def strlen(string: str) -> int:\n    pass",
        "tests": [
            ("strlen('')", 0),
            ("strlen('x')", 1),
            ("strlen('asdfghjkl')", 9),
        ],
    },
    # HumanEval/25
    {
        "he_id": 25,
        "name": "factorize",
        "description": (
            "Return list of prime factors of given integer in the order from smallest to largest.\n"
            "Each of the factors should be listed number of times corresponding to how many times it appears in factorization.\n"
            "Input number should be equal to the product of all factors.\n"
            ">>> factorize(8)\n"
            "[2, 2, 2]\n"
            ">>> factorize(25)\n"
            "[5, 5]\n"
            ">>> factorize(70)\n"
            "[2, 5, 7]"
        ),
        "before": "from typing import List\n\ndef factorize(n: int) -> List[int]:\n    pass",
        "tests": [
            ("factorize(2)", [2]),
            ("factorize(4)", [2, 2]),
            ("factorize(8)", [2, 2, 2]),
            ("factorize(57)", [3, 19]),
            ("factorize(3249)", [3, 3, 19, 19]),
            ("factorize(25)", [5, 5]),
            ("factorize(70)", [2, 5, 7]),
        ],
    },
    # HumanEval/26
    {
        "he_id": 26,
        "name": "remove_duplicates",
        "description": (
            "From a list of integers, remove all elements that occur more than once.\n"
            "Keep order of elements left the same as in the input.\n"
            ">>> remove_duplicates([1, 2, 3, 2, 4])\n"
            "[1, 3, 4]"
        ),
        "before": "from typing import List\n\ndef remove_duplicates(numbers: List[int]) -> List[int]:\n    pass",
        "tests": [
            ("remove_duplicates([])", []),
            ("remove_duplicates([1, 2, 3, 4])", [1, 2, 3, 4]),
            ("remove_duplicates([1, 2, 3, 2, 4, 3, 5])", [1, 4, 5]),
        ],
    },
    # HumanEval/27
    {
        "he_id": 27,
        "name": "flip_case",
        "description": (
            "For a given string, flip lowercase characters to uppercase and uppercase to lowercase.\n"
            ">>> flip_case('Hello')\n"
            "'hELLO'"
        ),
        "before": "def flip_case(string: str) -> str:\n    pass",
        "tests": [
            ("flip_case('')", ''),
            ("flip_case('Hello!')", 'hELLO!'),
            ("flip_case('These violent delights have violent ends')", 'tHESE VIOLENT DELIGHTS HAVE VIOLENT ENDS'),
        ],
    },
    # HumanEval/28
    {
        "he_id": 28,
        "name": "concatenate",
        "description": (
            "Concatenate list of strings into a single string.\n"
            ">>> concatenate([])\n"
            "''\n"
            ">>> concatenate(['a', 'b', 'c'])\n"
            "'abc'"
        ),
        "before": "from typing import List\n\ndef concatenate(strings: List[str]) -> str:\n    pass",
        "tests": [
            ("concatenate([])", ''),
            ("concatenate(['x', 'y', 'z'])", 'xyz'),
            ("concatenate(['x', 'y', 'z', 'w', 'k'])", 'xyzwk'),
        ],
    },
    # HumanEval/29
    {
        "he_id": 29,
        "name": "filter_by_prefix",
        "description": (
            "Filter an input list of strings only for ones that start with a given prefix.\n"
            ">>> filter_by_prefix([], 'a')\n"
            "[]\n"
            ">>> filter_by_prefix(['abc', 'bcd', 'cde', 'array'], 'a')\n"
            "['abc', 'array']"
        ),
        "before": "from typing import List\n\ndef filter_by_prefix(strings: List[str], prefix: str) -> List[str]:\n    pass",
        "tests": [
            ("filter_by_prefix([], 'john')", []),
            ("filter_by_prefix(['xxx', 'asd', 'xxy', 'john doe', 'xxxuj', 'xxx hijk'], 'xxx')", ['xxx', 'xxxuj', 'xxx hijk']),
        ],
    },
    # HumanEval/30
    {
        "he_id": 30,
        "name": "get_positive",
        "description": (
            "Return only positive numbers in the list.\n"
            ">>> get_positive([-1, 2, -4, 5, 6])\n"
            "[2, 5, 6]\n"
            ">>> get_positive([5, 3, -5, 2, -3, 3, 9, 0, 123, 1, -10])\n"
            "[5, 3, 2, 3, 9, 123, 1]"
        ),
        "before": "from typing import List\n\ndef get_positive(l: List[int]) -> List[int]:\n    pass",
        "tests": [
            ("get_positive([-1, -2, 4, 5, 6])", [4, 5, 6]),
            ("get_positive([5, 3, -5, 2, 3, 3, 9, 0, 123, 1, -10])", [5, 3, 2, 3, 3, 9, 123, 1]),
            ("get_positive([-1, -2])", []),
            ("get_positive([])", []),
        ],
    },
    # HumanEval/31
    {
        "he_id": 31,
        "name": "is_prime",
        "description": (
            "Return true if a given number is prime, and false otherwise.\n"
            ">>> is_prime(6)\n"
            "False\n"
            ">>> is_prime(101)\n"
            "True\n"
            ">>> is_prime(11)\n"
            "True\n"
            ">>> is_prime(1)\n"
            "False"
        ),
        "before": "def is_prime(n: int) -> bool:\n    pass",
        "tests": [
            ("is_prime(6)", False),
            ("is_prime(101)", True),
            ("is_prime(11)", True),
            ("is_prime(13441)", True),
            ("is_prime(61)", True),
            ("is_prime(4)", False),
            ("is_prime(1)", False),
        ],
    },
    # HumanEval/32
    {
        "he_id": 32,
        "name": "find_zero",
        "description": (
            "xs are coefficients of a polynomial. find_zero finds x such that poly(x) = 0.\n"
            "poly(xs, x) evaluates a polynomial with coefficients xs at point x.\n"
            "find_zero only takes list xs having even number of coefficients and largest non-zero coefficient\n"
            "as it guarantees a solution.\n"
            ">>> round(find_zero([1, 2]), 2)  # f(x) = 1 + 2*x\n"
            "-0.5\n"
            ">>> round(find_zero([-6, 11, -6, 1]), 2)  # (x-1)(x-2)(x-3) = -6+11x-6x^2+x^3\n"
            "1.0"
        ),
        "before": (
            "import math\n\n"
            "def poly(xs: list, x: float) -> float:\n"
            "    return sum([coeff * math.pow(x, i) for i, coeff in enumerate(xs)])\n\n"
            "def find_zero(xs: list) -> float:\n"
            "    pass"
        ),
        "tests": [
            ("abs(poly([1, 2], find_zero([1, 2]))) < 1e-4", True),
            ("abs(poly([-6, 11, -6, 1], find_zero([-6, 11, -6, 1]))) < 1e-4", True),
            ("abs(poly([2, 1], find_zero([2, 1]))) < 1e-4", True),
        ],
    },
    # HumanEval/34
    {
        "he_id": 34,
        "name": "unique",
        "description": (
            "Return sorted unique elements in a list.\n"
            ">>> unique([5, 3, 5, 2, 3, 3, 9, 0, 123])\n"
            "[0, 2, 3, 5, 9, 123]"
        ),
        "before": "from typing import List\n\ndef unique(l: List[int]) -> List[int]:\n    pass",
        "tests": [
            ("unique([5, 3, 5, 2, 3, 3, 9, 0, 123])", [0, 2, 3, 5, 9, 123]),
        ],
    },
    # HumanEval/10
    {
        "he_id": 10,
        "name": "make_palindrome",
        "description": (
            "Find the shortest palindrome that begins with a supplied string.\n"
            "Algorithm idea is simple:\n"
            "- Find the longest postfix of supplied string that is a palindrome.\n"
            "- Append to the end of the string reverse of a string prefix that comes before the palindromic suffix.\n"
            ">>> make_palindrome('')\n"
            "''\n"
            ">>> make_palindrome('cat')\n"
            "'catac'\n"
            ">>> make_palindrome('cata')\n"
            "'catac'"
        ),
        "before": "def make_palindrome(string: str) -> str:\n    pass",
        "tests": [
            ("make_palindrome('')", ''),
            ("make_palindrome('cat')", 'catac'),
            ("make_palindrome('cata')", 'catac'),
            ("make_palindrome('A')", 'A'),
            ("make_palindrome('xyx')", 'xyx'),
            ("make_palindrome('jerry')", 'jerryrrej'),
        ],
    },
    # HumanEval/19
    {
        "he_id": 19,
        "name": "sort_numbers",
        "description": (
            "Input is a space-delimited string of numberals from 'zero' to 'nine'.\n"
            "Valid choices are 'zero', 'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight' and 'nine'.\n"
            "Return the string with numbers sorted from smallest to largest.\n"
            ">>> sort_numbers('three one five')\n"
            "'one three five'"
        ),
        "before": "def sort_numbers(numbers: str) -> str:\n    pass",
        "tests": [
            ("sort_numbers('')", ''),
            ("sort_numbers('three')", 'three'),
            ("sort_numbers('three five nine')", 'three five nine'),
            ("sort_numbers('five zero four seven nine eight')", 'zero four five seven eight nine'),
            ("sort_numbers('six five four three two one zero')", 'zero one two three four five six'),
        ],
    },
    # HumanEval/33
    {
        "he_id": 33,
        "name": "sort_third",
        "description": (
            "This function takes a list l and returns a list l' such that\n"
            "l' is identical to l in the indices that are not divisible by three, while its values at the indices\n"
            "that are divisible by three are equal to the values of the corresponding indices of l, but sorted.\n"
            ">>> sort_third([1, 2, 3])\n"
            "[1, 2, 3]\n"
            ">>> sort_third([5, 6, 3, 4, 8, 9, 2])\n"
            "[2, 6, 3, 4, 8, 9, 5]"
        ),
        "before": "from typing import List\n\ndef sort_third(l: List[int]) -> List[int]:\n    pass",
        "tests": [
            ("sort_third([1, 2, 3])", [1, 2, 3]),
            ("sort_third([5, 6, 3, 4, 8, 9, 2])", [2, 6, 3, 4, 8, 9, 5]),
            ("sort_third([5, 8, 3, 4, 6, 9, 2])", [2, 8, 3, 4, 6, 9, 5]),
            ("sort_third([5, 6, 9, 4, 8, 3, 2])", [2, 6, 9, 4, 8, 3, 5]),
        ],
    },
    # HumanEval/36
    {
        "he_id": 36,
        "name": "fizz_buzz",
        "description": (
            "Return the number of times the digit 7 appears in integers less than n which are divisible by 11 or 13.\n"
            ">>> fizz_buzz(50)\n"
            "0\n"
            ">>> fizz_buzz(78)\n"
            "2\n"
            ">>> fizz_buzz(79)\n"
            "3"
        ),
        "before": "def fizz_buzz(n: int) -> int:\n    pass",
        "tests": [
            ("fizz_buzz(50)", 0),
            ("fizz_buzz(78)", 2),
            ("fizz_buzz(79)", 3),
            ("fizz_buzz(100)", 3),
            ("fizz_buzz(200)", 6),
            ("fizz_buzz(4000)", 192),
        ],
    },
    # HumanEval/37
    {
        "he_id": 37,
        "name": "sort_even",
        "description": (
            "This function takes a list l and returns a list l' such that\n"
            "l' is identical to l in the odd indices, while its values at the even indices are equal\n"
            "to the values of the even indices of l, but sorted.\n"
            ">>> sort_even([1, 2, 3])\n"
            "[1, 2, 3]\n"
            ">>> sort_even([5, 6, 3, 4])\n"
            "[3, 6, 5, 4]"
        ),
        "before": "from typing import List\n\ndef sort_even(l: List[int]) -> List[int]:\n    pass",
        "tests": [
            ("sort_even([1, 2, 3])", [1, 2, 3]),
            ("sort_even([5, 6, 3, 4])", [3, 6, 5, 4]),
            ("sort_even([5, 3, -5, 2, -3, 3, 9, 0, 123])", [-5, 3, -3, 2, 5, 3, 9, 0, 123]),
        ],
    },
    # HumanEval/39
    {
        "he_id": 39,
        "name": "prime_fib",
        "description": (
            "prime_fib returns n-th number that is a Fibonacci number and it's also prime.\n"
            ">>> prime_fib(1)\n"
            "2\n"
            ">>> prime_fib(2)\n"
            "3\n"
            ">>> prime_fib(3)\n"
            "5\n"
            ">>> prime_fib(4)\n"
            "13\n"
            ">>> prime_fib(5)\n"
            "89"
        ),
        "before": "def prime_fib(n: int) -> int:\n    pass",
        "tests": [
            ("prime_fib(1)", 2),
            ("prime_fib(2)", 3),
            ("prime_fib(3)", 5),
            ("prime_fib(4)", 13),
            ("prime_fib(5)", 89),
        ],
    },
    # HumanEval/40
    {
        "he_id": 40,
        "name": "triples_sum_to_zero",
        "description": (
            "triples_sum_to_zero takes a list of integers as an input.\n"
            "it returns True if there are three distinct elements in the list that sum to zero, and False otherwise.\n"
            ">>> triples_sum_to_zero([1, 3, 5, 0])\n"
            "False\n"
            ">>> triples_sum_to_zero([1, 3, -2, 1])\n"
            "True\n"
            ">>> triples_sum_to_zero([1, 2, 3, 7])\n"
            "False\n"
            ">>> triples_sum_to_zero([2, 4, -5, 3, 9, 7])\n"
            "True"
        ),
        "before": "from typing import List\n\ndef triples_sum_to_zero(l: List[int]) -> bool:\n    pass",
        "tests": [
            ("triples_sum_to_zero([1, 3, 5, 0])", False),
            ("triples_sum_to_zero([1, 3, -2, 1])", True),
            ("triples_sum_to_zero([1, 2, 3, 7])", False),
            ("triples_sum_to_zero([2, 4, -5, 3, 9, 7])", True),
            ("triples_sum_to_zero([1])", False),
        ],
    },
    # HumanEval/43
    {
        "he_id": 43,
        "name": "pairs_sum_to_zero",
        "description": (
            "pairs_sum_to_zero takes a list of integers as an input.\n"
            "it returns True if there are two distinct elements in the list that sum to zero, and False otherwise.\n"
            ">>> pairs_sum_to_zero([1, 3, 5, 0])\n"
            "False\n"
            ">>> pairs_sum_to_zero([1, 3, -2, 1])\n"
            "False\n"
            ">>> pairs_sum_to_zero([1, 2, 3, 7])\n"
            "False\n"
            ">>> pairs_sum_to_zero([2, 4, -5, 3, 5, 7])\n"
            "True"
        ),
        "before": "from typing import List\n\ndef pairs_sum_to_zero(l: List[int]) -> bool:\n    pass",
        "tests": [
            ("pairs_sum_to_zero([1, 3, 5, 0])", False),
            ("pairs_sum_to_zero([1, 3, -2, 1])", False),
            ("pairs_sum_to_zero([1, 2, 3, 7])", False),
            ("pairs_sum_to_zero([2, 4, -5, 3, 5, 7])", True),
            ("pairs_sum_to_zero([1])", False),
        ],
    },
    # HumanEval/44
    {
        "he_id": 44,
        "name": "change_base",
        "description": (
            "Change numerical base of input number x to base.\n"
            "return string representation after the conversion.\n"
            "base numbers are less than 10.\n"
            ">>> change_base(8, 3)\n"
            "'22'\n"
            ">>> change_base(8, 2)\n"
            "'1000'\n"
            ">>> change_base(7, 2)\n"
            "'111'"
        ),
        "before": "def change_base(x: int, base: int) -> str:\n    pass",
        "tests": [
            ("change_base(8, 3)", '22'),
            ("change_base(8, 2)", '1000'),
            ("change_base(7, 2)", '111'),
            ("change_base(234, 2)", '11101010'),
            ("change_base(16, 2)", '10000'),
            ("change_base(8, 8)", '10'),
            ("change_base(0, 5)", '0'),
        ],
    },
    # HumanEval/46
    {
        "he_id": 46,
        "name": "fib4",
        "description": (
            "The Fib4 number sequence is a sequence similar to the Fibonacci sequence that's defined as follows:\n"
            "fib4(0) -> 0\n"
            "fib4(1) -> 0\n"
            "fib4(2) -> 2\n"
            "fib4(3) -> 0\n"
            "fib4(n) -> fib4(n-1) + fib4(n-2) + fib4(n-3) + fib4(n-4)\n"
            "Please write a function to efficiently compute the n-th element of the fib4 number sequence. Do not use recursion.\n"
            ">>> fib4(5)\n"
            "4\n"
            ">>> fib4(6)\n"
            "8\n"
            ">>> fib4(7)\n"
            "14"
        ),
        "before": "def fib4(n: int) -> int:\n    pass",
        "tests": [
            ("fib4(5)", 4),
            ("fib4(6)", 8),
            ("fib4(7)", 14),
            ("fib4(8)", 28),
            ("fib4(10)", 104),
        ],
    },
    # HumanEval/47
    {
        "he_id": 47,
        "name": "median",
        "description": (
            "Return median of elements in the list l.\n"
            ">>> median([3, 1, 2, 4, 5])\n"
            "3\n"
            ">>> median([-10, 4, 6, 1000, 10, 20])\n"
            "15.0"
        ),
        "before": "from typing import List, Union\n\ndef median(l: List[int]) -> Union[int, float]:\n    pass",
        "tests": [
            ("median([3, 1, 2, 4, 5])", 3),
            ("median([-10, 4, 6, 1000, 10, 20])", 15.0),
            ("median([5])", 5),
            ("median([6, 5])", 5.5),
            ("median([8, 1, 3, 9, 9, 2, 7])", 7),
        ],
    },
    # HumanEval/49
    {
        "he_id": 49,
        "name": "modp",
        "description": (
            "Return 2^n modulo p (be aware of numerics).\n"
            ">>> modp(3, 5)\n"
            "3\n"
            ">>> modp(1101, 101)\n"
            "2\n"
            ">>> modp(0, 101)\n"
            "1\n"
            ">>> modp(3, 11)\n"
            "8\n"
            ">>> modp(100, 101)\n"
            "1"
        ),
        "before": "def modp(n: int, p: int) -> int:\n    pass",
        "tests": [
            ("modp(3, 5)", 3),
            ("modp(1101, 101)", 2),
            ("modp(0, 101)", 1),
            ("modp(3, 11)", 8),
            ("modp(100, 101)", 1),
        ],
    },
    # HumanEval/59
    {
        "he_id": 59,
        "name": "largest_prime_factor",
        "description": (
            "Return the largest prime factor of n. Assume n > 1 and is not a prime.\n"
            ">>> largest_prime_factor(13195)\n"
            "29\n"
            ">>> largest_prime_factor(2048)\n"
            "2"
        ),
        "before": "def largest_prime_factor(n: int) -> int:\n    pass",
        "tests": [
            ("largest_prime_factor(15)", 5),
            ("largest_prime_factor(13195)", 29),
            ("largest_prime_factor(2048)", 2),
            ("largest_prime_factor(6)", 3),
            ("largest_prime_factor(49)", 7),
        ],
    },
    # HumanEval/62
    {
        "he_id": 62,
        "name": "derivative",
        "description": (
            "xs represent coefficients of a polynomial.\n"
            "xs[0] + xs[1] * x + xs[2] * x^2 + ....\n"
            "Return derivative of this polynomial in the same form.\n"
            ">>> derivative([3, 1, 2, 4, 5])\n"
            "[1, 4, 12, 20]\n"
            ">>> derivative([1, 2, 3])\n"
            "[2, 6]"
        ),
        "before": "from typing import List\n\ndef derivative(xs: List[int]) -> List[int]:\n    pass",
        "tests": [
            ("derivative([3, 1, 2, 4, 5])", [1, 4, 12, 20]),
            ("derivative([1, 2, 3])", [2, 6]),
            ("derivative([3, 1])", [1]),
            ("derivative([3])", []),
        ],
    },
    # HumanEval/63
    {
        "he_id": 63,
        "name": "fibfib",
        "description": (
            "The FibFib number sequence is a sequence similar to the Fibonacci sequence that's defined as follows:\n"
            "fibfib(0) == 0\n"
            "fibfib(1) == 0\n"
            "fibfib(2) == 1\n"
            "fibfib(n) == fibfib(n-1) + fibfib(n-2) + fibfib(n-3).\n"
            "Please write a function to efficiently compute the n-th element of the fibfib number sequence.\n"
            ">>> fibfib(1)\n"
            "0\n"
            ">>> fibfib(5)\n"
            "4\n"
            ">>> fibfib(8)\n"
            "24"
        ),
        "before": "def fibfib(n: int) -> int:\n    pass",
        "tests": [
            ("fibfib(2)", 1),
            ("fibfib(1)", 0),
            ("fibfib(5)", 4),
            ("fibfib(8)", 24),
            ("fibfib(10)", 81),
        ],
    },
    # HumanEval/69
    {
        "he_id": 69,
        "name": "search",
        "description": (
            "You are given a non-empty list of positive integers. Return the greatest integer that is greater than\n"
            "zero, and has a frequency greater than or equal to the value of the integer itself.\n"
            "The frequency of an integer is the number of times it appears in the list.\n"
            "If no such a value exist, return -1.\n"
            ">>> search([4, 1, 2, 2, 3, 1])\n"
            "2\n"
            ">>> search([1, 2, 2, 3, 3, 3, 4, 4, 4])\n"
            "3\n"
            ">>> search([5, 5, 4, 4, 4])\n"
            "-1"
        ),
        "before": "from typing import List\n\ndef search(lst: List[int]) -> int:\n    pass",
        "tests": [
            ("search([4, 1, 2, 2, 3, 1])", 2),
            ("search([1, 2, 2, 3, 3, 3, 4, 4, 4])", 3),
            ("search([5, 5, 4, 4, 4])", -1),
            ("search([2, 3, 3, 2, 2])", 2),
            ("search([1])", 1),
        ],
    },
    # HumanEval/72
    {
        "he_id": 72,
        "name": "will_it_fly",
        "description": (
            "Write a function that returns True if the object q will fly, and False otherwise.\n"
            "The object q will fly if it's balanced (it is a palindromic list) and the sum of its elements is\n"
            "less than or equal the maximum possible weight w.\n"
            ">>> will_it_fly([1, 2], 5)\n"
            "False\n"
            ">>> will_it_fly([3, 2, 3], 1)\n"
            "False\n"
            ">>> will_it_fly([3, 2, 3], 9)\n"
            "True\n"
            ">>> will_it_fly([3], 5)\n"
            "True"
        ),
        "before": "from typing import List\n\ndef will_it_fly(q: List[int], w: int) -> bool:\n    pass",
        "tests": [
            ("will_it_fly([1, 2], 5)", False),
            ("will_it_fly([3, 2, 3], 1)", False),
            ("will_it_fly([3, 2, 3], 9)", True),
            ("will_it_fly([3], 5)", True),
            ("will_it_fly([3, 2, 3], 8)", True),
        ],
    },
    # HumanEval/75
    {
        "he_id": 75,
        "name": "is_multiply_prime",
        "description": (
            "Write a function that returns true if the given number is the multiplication of 3 prime numbers\n"
            "and false otherwise.\n"
            "Knowing that (a) is less then 100.\n"
            ">>> is_multiply_prime(30)\n"
            "True\n"
            "30 = 2 * 3 * 5"
        ),
        "before": "def is_multiply_prime(a: int) -> bool:\n    pass",
        "tests": [
            ("is_multiply_prime(5)", False),
            ("is_multiply_prime(30)", True),
            ("is_multiply_prime(8)", True),
            ("is_multiply_prime(10)", False),
            ("is_multiply_prime(27)", True),
            ("is_multiply_prime(66)", False),
        ],
    },
    # HumanEval/77
    {
        "he_id": 77,
        "name": "iscube",
        "description": (
            "Write a function that takes an integer a and returns True if this integer is a cube of some integer number.\n"
            "Note: you may assume the input is always valid.\n"
            ">>> iscube(1)\n"
            "True\n"
            ">>> iscube(2)\n"
            "False\n"
            ">>> iscube(-1)\n"
            "True\n"
            ">>> iscube(64)\n"
            "True\n"
            ">>> iscube(0)\n"
            "True\n"
            ">>> iscube(180)\n"
            "False"
        ),
        "before": "def iscube(a: int) -> bool:\n    pass",
        "tests": [
            ("iscube(1)", True),
            ("iscube(2)", False),
            ("iscube(-1)", True),
            ("iscube(64)", True),
            ("iscube(0)", True),
            ("iscube(180)", False),
            ("iscube(-8)", True),
        ],
    },
    # HumanEval/80
    {
        "he_id": 80,
        "name": "is_happy",
        "description": (
            "You are given a string s.\n"
            "Your task is to check if the string is happy or not.\n"
            "A string is happy if its length is at least 3 and every 3 consecutive letters are distinct.\n"
            ">>> is_happy('a')\n"
            "False\n"
            ">>> is_happy('aa')\n"
            "False\n"
            ">>> is_happy('abcd')\n"
            "True\n"
            ">>> is_happy('aabb')\n"
            "False\n"
            ">>> is_happy('adb')\n"
            "True\n"
            ">>> is_happy('xyy')\n"
            "False"
        ),
        "before": "def is_happy(s: str) -> bool:\n    pass",
        "tests": [
            ("is_happy('a')", False),
            ("is_happy('aa')", False),
            ("is_happy('abcd')", True),
            ("is_happy('aabb')", False),
            ("is_happy('adb')", True),
            ("is_happy('xyy')", False),
            ("is_happy('iopaxpoi')", True),
        ],
    },
]


def run_humaneval_tests(after_code: str, task: dict) -> dict:
    """1問のHumanEvalタスクを評価し、結果を返す"""
    tests = task["tests"]
    result = {
        "he_id": task["he_id"],
        "name": task["name"],
        "total": len(tests),
        "passed": 0,
        "error": None,
    }

    # 構文チェック
    try:
        ast.parse(after_code)
    except SyntaxError as e:
        result["error"] = f"SyntaxError: {e}"
        return result

    # コード実行
    namespace = {}
    try:
        exec(after_code, namespace)
    except Exception as e:
        result["error"] = f"ExecError: {e}"
        return result

    # テスト実行
    passed = 0
    for test_expr, expected in tests:
        try:
            actual = eval(test_expr, namespace)
            if actual == expected:
                passed += 1
        except Exception:
            pass

    result["passed"] = passed
    return result


def run_all_humaneval() -> list[dict]:
    """全50問を問題文のみで（LLM無し）ダミー実行用。実際はrun_benchmark.pyから呼ぶ。"""
    return HUMANEVAL_TASKS
