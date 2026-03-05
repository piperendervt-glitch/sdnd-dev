def get_last(lst):
    """
    Gets the last element from a list.

    Parameters:
    lst (list): The list from which to get the last element.

    Returns:
    The last element of the list if the list is not empty, otherwise None.
    """
    # Fix: lst[-1] に修正
    if lst:  # Check if the list is not empty
        return lst[-1]
    else:
        return None