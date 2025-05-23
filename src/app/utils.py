

def validate_retention_period(retention_period: str):
    """
    Validate the retention period format.

    Args:
        retention_period (str): The retention period string to validate.

    Returns:
        None: If the retention period is valid.
    """
    if retention_period < 0:
        raise ValueError("Retention must be a non-negative integer.")
    if retention_period > 30:
        raise ValueError("Retention must be less than or equal to 30.")
    if not isinstance(retention_period, int):
        raise TypeError("Retention must be an integer.")
    
