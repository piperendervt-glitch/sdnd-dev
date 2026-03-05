def divide(a, b):
    """
    ファクションの説明。

    Args:
        a: 引数の説明
        b: 引数の説明

    Returns:
        戻り値の説明

    Raises:
        ZeroDivisionError: b が 0 の場合、このエラーがスローされる
    """
    if b == 0:
        raise ZeroDivisionError("b が 0 の場合、割り算は実行できません")
    return a / b