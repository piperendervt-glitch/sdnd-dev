def get_last(lst):
    """リストの最後の要素を返す。

    Args:
        lst: 列挙型のリスト

    Returns:
        列挿型のリストの最後の要素
    """
    if not lst:
        return None
    return lst[-1]