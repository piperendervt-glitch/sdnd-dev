def divide(a, b):
    """関数の説明。

    Args:
        a: 被除数
        b: 除数

    Returns:
        戻り値の説明

    Raises:
        ValueError: b が 0 の場合
    """
    if b == 0:
        raise ValueError("b (除数) が 0 に設定されています。")
    return a / b