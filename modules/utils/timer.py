import time

__all__ = (
    'Timer',
)


class Timer:
    def __init__(self):
        self.a, self.b, = 0, 0

    def __enter__(self):
        self.a = time.perf_counter()
        return self

    def __exit__(self, *error):
        self.b = time.perf_counter()
        self.t = self.b - self.a
        return self
