import time
from functools import wraps

from metermind.core.exceptions import InvalidReadingError


def reject_negative_readings(wrapped_function):
    @wraps(wrapped_function)
    def wrapper(*args, **kwargs):
        for value in list(args) + list(kwargs.values()):
            if (
                isinstance(value, (int, float))
                and not isinstance(value, bool)
                and value < 0
            ):
                raise InvalidReadingError(
                    f"{wrapped_function.__name__}: negative value {value}"
                )
        return wrapped_function(*args, **kwargs)

    return wrapper


def measure_execution_duration(wrapped_function):
    @wraps(wrapped_function)
    def wrapper(*args, **kwargs):
        started = time.perf_counter()
        result = wrapped_function(*args, **kwargs)
        wrapper.last_duration_seconds = time.perf_counter() - started
        return result

    wrapper.last_duration_seconds = 0.0
    return wrapper


if __name__ == "__main__":

    @measure_execution_duration
    def add_up(values):
        return sum(values)

    result = add_up([1, 2, 3])
    print(
        f"add_up([1, 2, 3]) returned {result} and the wrapper timed it at "
        f"{add_up.last_duration_seconds:.6f} seconds"
    )
