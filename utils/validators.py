import warnings


def validate_condition(condition, msg: str = None, warn_only=False):
    """
    Validates if condition holds, raises ValueError otherwise.

    :param condition: The condition
    :param msg: (Optionally) An error message
    :raises ValueError: If condition does not hold
    :param warn_only: If just a non-interrupting warning should be given.
    """
    if condition:
        return
    if msg is None:
        msg = ""
    if not warn_only:
        raise ValueError(msg)
    warnings.warn(msg)
