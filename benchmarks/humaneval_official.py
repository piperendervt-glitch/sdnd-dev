"""HumanEval公式30問ベンチマーク（純粋実力測定用）

HumanEval 164問からeasy〜medium難易度の30問を選定。
task_pool.jsonには連携しない測定専用ベンチマーク。

評価方法: unittest通過率（pass@1）
"""

from __future__ import annotations

import ast
import traceback

# ─────────────────────────────────────────
# 30問定義（HumanEval公式問題番号付き）
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
    """全30問を問題文のみで（LLM無し）ダミー実行用。実際はrun_benchmark.pyから呼ぶ。"""
    return HUMANEVAL_TASKS
