def divide(a, b):
    """
    Parameters:
    a (float): The dividend.
    b (float): The divisor.

    Returns:
    float: The result of the division.

    Raises:
    ZeroDivisionError: If the divisor b is zero.
    """
    if b == 0:
        raise ZeroDivisionError("Division by zero is not allowed.")
    return a / b