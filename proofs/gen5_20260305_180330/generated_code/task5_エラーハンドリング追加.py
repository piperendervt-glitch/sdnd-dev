def divide(a, b):
    """
    Args:
        a: 被除数
        b: 除数
    Returns:
        a と b の除算結果
    Raises:
        ZeroDivisionError: b が 0 の場合
    """
    try:
        return a / b
    except ZeroDivisionError:
        raise ZeroDivisionError("b は 0 個体で割ることはできません。")