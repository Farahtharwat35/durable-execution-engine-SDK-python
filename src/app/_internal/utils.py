def validate_retention_period(retention: int) -> None:
    """
    Validate that the retention period is a non-negative integer.

    Args:
        retention (int): The retention period in days.

    Raises:
        ValueError: If the retention period is not a non-negative integer.
    """
    if not isinstance(retention, int):
        raise ValueError("Retention period must be an integer.")
    if retention < 0:
        raise ValueError("Retention period must be a non-negative integer.")
    if retention > 30:
        raise ValueError("Retention period cannot exceed 30 days.")
