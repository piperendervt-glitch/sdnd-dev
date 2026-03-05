def divide(a, b):
    """
    実数 a, b の除算を返す関数。

    Args:
        a (float): 被除算数
        b (float): 除算数

    Returns:
        float: a / b

    Raises:
        ZeroDivisionError: b が 0 の場合
    """
    if b == 0:
        raise ZeroDivisionError("除算数が 0 に設定されています。")
    return a / b