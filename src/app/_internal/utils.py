from typing import Any
from dataclasses import is_dataclass, asdict
from pydantic import BaseModel


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


def serialize_data(data: Any) -> Any:
    """
    Recursively serialize Pydantic models and dataclasses to JSON-compatible dictionaries.
    
    Args:
        data: The data to serialize (can be any type)
        
    Returns:
        The serialized data with all Pydantic models/dataclasses converted to dicts
        
    Examples:
        >>> serialize_data(UserModel(name="John", age=30))
        {"name": "John", "age": 30}
        
        >>> serialize_data({"user": UserModel(name="John"), "count": 5})
        {"user": {"name": "John"}, "count": 5}
        
        >>> serialize_data([UserModel(name="John"), UserModel(name="Jane")])
        [{"name": "John"}, {"name": "Jane"}]
    """
    if isinstance(data, BaseModel):
        # Handle both Pydantic v1 (.dict()) and v2 (.model_dump())
        if hasattr(data, 'model_dump'):
            return data.model_dump()
        elif hasattr(data, 'dict'):
            return data.dict()
        else:
            # Fallback: try to convert to dict manually
            return {field: getattr(data, field) for field in data.__fields__}
    elif is_dataclass(data):
        return asdict(data)
    elif isinstance(data, dict):
        return {key: serialize_data(value) for key, value in data.items()}
    elif isinstance(data, list):
        return [serialize_data(item) for item in data]
    elif isinstance(data, tuple):
        return tuple(serialize_data(item) for item in data)
    else:
        return data
