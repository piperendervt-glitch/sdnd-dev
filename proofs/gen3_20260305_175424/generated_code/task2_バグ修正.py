def get_last(lst):
    if not lst:  # 空リストのエラーを防ぐ
        return None
    return lst[-1]  # off-by-oneエラーを修正