def validate_condition(condition, msg: str = None):
    """
    Validates if condition holds, raises ValueError otherwise.

    :param condition: The condition.
    :param msg: (Optionally) An error message.
    :raises ValueError: If condition does not hold.
    """
    if not condition:
        if msg is not None:
            raise ValueError(msg)
        raise ValueError()
