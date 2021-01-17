def time_to_readable_string(time_in_seconds: float) -> str:
    """
    Given a length of time in seconds (as a float), returns a human readable
    string describing the time. For times less than 60 seconds, this method
    will show fractional components.
    """
    if time_in_seconds < 60:
        return "{:.2f} seconds".format(time_in_seconds)

    seconds_int = round(time_in_seconds)
    time_components = []

    for unit, count in _intervals:
        amount = seconds_int // count
        if amount <= 0:
            continue
        seconds_int -= amount * count
        if amount == 1:
            time_components.append("{} {}".format(amount, unit.rstrip("s")))
        else:
            time_components.append("{} {}".format(amount, unit))

    if len(time_components) == 1:
        return time_components[0]
    elif len(time_components) == 2:
        return " and ".join(time_components)
    else:
        return "{}, and {}".format(", ".join(time_components[:-1]), time_components[-1])


_intervals = [
    ("days", 86400),  # 60 * 60 * 24
    ("hours", 3600),  # 60 * 60
    ("minutes", 60),
    ("seconds", 1),
]
