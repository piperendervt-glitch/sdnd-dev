def divide(a, b):
    """
    Args:
        a: 被除数
        b: 除数

    Returns:
        a / b の結果

    Raises:
        ZeroDivisionError: b が 0 の場合
    """
    try:
        return a / b
    except ZeroDivisionError:
        raise ZeroDivisionError("除数 b が 0 であるため、割り算はできません。")