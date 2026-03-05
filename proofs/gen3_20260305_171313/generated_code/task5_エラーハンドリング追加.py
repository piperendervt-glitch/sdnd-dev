def divide(a, b):
    """
    Function to divide two numbers.
    
    Args:
    a (float): The numerator of the division.
    b (float): The denominator of the division.
    
    Returns:
    float: The result of the division.
    
    Raises:
    ZeroDivisionError: If the denominator b is zero.
    """
    if b == 0:
        raise ZeroDivisionError("Denominator cannot be zero.")
    return a / b