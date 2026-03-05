def get_last(lst):
    """
    Returns the last element of the given list.

    Parameters:
    lst (list): The list from which the last element is to be retrieved.

    Returns:
    Any: The last element of the list. If the list is empty, returns None.
    """
    if not lst:
        return None
    return lst[-1]