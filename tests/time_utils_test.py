from conductor.utils.time import time_to_readable_string


def test_less_than_one_minute():
    assert time_to_readable_string(1.1) == "1.10 seconds"
    assert time_to_readable_string(0.12) == "0.12 seconds"


def test_time_zero():
    assert time_to_readable_string(0.0) == "0.00 seconds"


def test_time_minute():
    assert time_to_readable_string(60.1) == "1 minute"
    assert time_to_readable_string(60.8) == "1 minute and 1 second"


def test_time_multi_minutes():
    assert time_to_readable_string(190.1) == "3 minutes and 10 seconds"


def test_time_hours():
    assert time_to_readable_string(3600.1) == "1 hour"
    assert time_to_readable_string(3660.1) == "1 hour and 1 minute"
    assert time_to_readable_string(3680.1) == "1 hour, 1 minute, and 20 seconds"
    assert time_to_readable_string(7210.8) == "2 hours and 11 seconds"


def test_time_days():
    assert time_to_readable_string(86400.1) == "1 day"
    assert time_to_readable_string(86430.0) == "1 day and 30 seconds"
    assert time_to_readable_string(172800.0) == "2 days"
    assert time_to_readable_string(172860.0) == "2 days and 1 minute"
    assert time_to_readable_string(172865.0) == "2 days, 1 minute, and 5 seconds"
