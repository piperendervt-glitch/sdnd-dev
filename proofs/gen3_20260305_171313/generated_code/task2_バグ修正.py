def get_last(lst):
    """Return the last item of the given list.

    Args:
        lst (list): The list from which to get the last item.

    Returns:
        The last item of the list if the list is not empty, otherwise None.
    """
    if not lst:
        return None
    return lst[-1]